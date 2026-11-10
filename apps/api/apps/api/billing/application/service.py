from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

import httpx
from apps.api.billing.domain import SubscriptionStatus
from apps.api.billing.infrastructure.models import Subscription
from apps.api.billing.infrastructure.repositories import (
    PayPalWebhookEventRepository,
    SubscriptionRepository,
)
from apps.api.identity.infrastructure.models import Organization
from apps.api.integrations.infrastructure.models import PayPalWebhookEvent
from apps.api.operations.application.audit import record_audit_event
from apps.api.settings import settings
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid

logger = logging.getLogger(__name__)
MAX_PAYPAL_WEBHOOK_BODY_BYTES = 1_000_000


def verify_stripe_signature(payload: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    secret = getattr(settings, "stripe_webhook_secret", "")
    if not secret:
        return False
    values: dict[str, str] = {}
    for part in signature.split(","):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        values[key.strip()] = value.strip()
    timestamp = values.get("t")
    expected_signature = values.get("v1")
    if not timestamp or not expected_signature:
        return False
    signed_payload = timestamp.encode("ascii") + b"." + payload
    actual_signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(actual_signature, expected_signature)


_SUBSCRIPTION_EVENTS = {
    "BILLING.SUBSCRIPTION.CREATED",
    "BILLING.SUBSCRIPTION.ACTIVATED",
    "BILLING.SUBSCRIPTION.UPDATED",
    "BILLING.SUBSCRIPTION.SUSPENDED",
    "BILLING.SUBSCRIPTION.CANCELLED",
    "BILLING.SUBSCRIPTION.EXPIRED",
    "BILLING.SUBSCRIPTION.PAYMENT.FAILED",
}
_PAYPAL_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class PayPalUnavailableError(Exception):
    pass


class PayPalPlanNotConfiguredError(Exception):
    pass


class PayPalSubscriptionConflictError(Exception):
    pass


class PayPalSubscriptionNotFoundError(Exception):
    pass


class PayPalOrganizationNotFoundError(Exception):
    pass


class PayPalSignatureError(Exception):
    pass


class PayPalWebhookPayloadError(Exception):
    pass


class PayPalBillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subscriptions = SubscriptionRepository(session)
        self.events = PayPalWebhookEventRepository(session)

    async def get_subscription(self, organization_id: str) -> Subscription | None:
        return await self.subscriptions.get_latest_for_org(organization_id)


    async def create_checkout_session(
        self,
        organization_id: str,
        user_email: str,
        plan_id: str,
        *,
        user_id: str,
        idempotency_key: str,
        trace_id: str,
    ) -> dict[str, str]:
        paypal_plan_id = settings.paypal_plan_ids.get(plan_id)
        if not paypal_plan_id:
            raise PayPalPlanNotConfiguredError
        self._require_api_configuration()

        organization_result = await self.session.execute(
            select(Organization)
            .where(Organization.id == organization_id)
            .with_for_update(of=Organization)
        )
        if organization_result.scalar_one_or_none() is None:
            raise PayPalOrganizationNotFoundError

        current = await self.subscriptions.get_latest_for_org(organization_id)
        if current is not None and current.status in {"active", "past_due", "trialing"}:
            raise PayPalSubscriptionConflictError
        if current is not None and current.status == "unpaid":
            if not current.paypal_subscription_id or not current.paypal_approval_url:
                raise PayPalSubscriptionConflictError
            return {
                "subscription_id": current.paypal_subscription_id,
                "url": current.paypal_approval_url,
            }

        request_id = hashlib.sha256(
            f"{organization_id}:{user_id}:{plan_id}:{idempotency_key}".encode()
        ).hexdigest()[:36]
        body = await self._paypal_request(
            "POST",
            "/v1/billing/subscriptions",
            {
                "plan_id": paypal_plan_id,
                "custom_id": organization_id,
                "subscriber": {"email_address": user_email},
                "application_context": {
                    "brand_name": "ChronoArb",
                    "locale": "en-US",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "SUBSCRIBE_NOW",
                    "return_url": settings.paypal_return_url,
                    "cancel_url": settings.paypal_cancel_url,
                },
            },
            request_id=request_id,
        )
        subscription_id = body.get("id")
        approval_url = self._approval_url(body)
        if not isinstance(subscription_id, str) or not _PAYPAL_ID_PATTERN.fullmatch(
            subscription_id
        ):
            raise PayPalUnavailableError
        if approval_url is None:
            raise PayPalUnavailableError

        subscription = Subscription(
            id=generate_ulid("sub"),
            organization_id=organization_id,
            paypal_subscription_id=subscription_id,
            paypal_approval_url=approval_url,
            status="unpaid",
            plan_id=plan_id,
        )
        self.session.add(subscription)
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="billing.paypal_subscription_created",
            resource_type="subscription",
            resource_id=subscription.id,
            details={"plan_id": plan_id, "paypal_subscription_id": subscription_id},
            trace_id=trace_id,
        )
        await self.session.commit()
        return {"subscription_id": subscription_id, "url": approval_url}

    async def cancel_subscription(
        self,
        organization_id: str,
        user_id: str,
        idempotency_key: str,
        *,
        trace_id: str,
    ) -> Subscription:
        self._require_api_configuration()
        organization_result = await self.session.execute(
            select(Organization)
            .where(Organization.id == organization_id)
            .with_for_update(of=Organization)
        )
        if organization_result.scalar_one_or_none() is None:
            raise PayPalSubscriptionNotFoundError
        subscription = await self.subscriptions.get_latest_for_org(organization_id)
        if subscription is None or subscription.paypal_subscription_id is None:
            raise PayPalSubscriptionNotFoundError
        if subscription.status == "canceled":
            return subscription

        await self._paypal_request(
            "POST",
            f"/v1/billing/subscriptions/{subscription.paypal_subscription_id}/cancel",
            {"reason": "Canceled by organization"},
            request_id=hashlib.sha256(
                f"{organization_id}:{user_id}:cancel:{idempotency_key}".encode()
            ).hexdigest()[:36],
        )
        subscription.status = "canceled"
        subscription.paypal_updated_at = datetime.now(UTC)
        subscription.updated_at = datetime.now(UTC)
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="billing.paypal_subscription_canceled",
            resource_type="subscription",
            resource_id=subscription.id,
            details={"paypal_subscription_id": subscription.paypal_subscription_id},
            trace_id=trace_id,
        )
        await self.session.commit()
        return subscription

    async def process_webhook(self, payload: bytes, headers: dict[str, str]) -> bool:
        if len(payload) > MAX_PAYPAL_WEBHOOK_BODY_BYTES:
            raise PayPalWebhookPayloadError
        self._require_api_configuration()
        if not settings.paypal_webhook_id:
            raise PayPalUnavailableError
        try:
            event: object = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise PayPalWebhookPayloadError from error
        if not isinstance(event, dict):
            raise PayPalWebhookPayloadError
        event_id = event.get("id")
        event_type = event.get("event_type")
        if not isinstance(event_id, str) or not event_id:
            raise PayPalWebhookPayloadError
        if not isinstance(event_type, str) or not event_type:
            raise PayPalWebhookPayloadError

        await self._verify_webhook_signature(event, headers)
        if await self.events.get_by_id(event_id) is not None:
            return False

        try:
            if event_type in _SUBSCRIPTION_EVENTS:
                await self._apply_subscription_update(event, event_type)
            self.session.add(PayPalWebhookEvent(id=event_id, event_type=event_type))
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            if await self.events.get_by_id(event_id) is not None:
                return False
            raise
        return True

    async def _verify_webhook_signature(
        self,
        event: dict[str, Any],
        headers: dict[str, str],
    ) -> None:
        required_headers = (
            "paypal-auth-algo",
            "paypal-cert-url",
            "paypal-transmission-id",
            "paypal-transmission-sig",
            "paypal-transmission-time",
        )
        if any(not headers.get(name) for name in required_headers):
            raise PayPalSignatureError
        verification = await self._paypal_request(
            "POST",
            "/v1/notifications/verify-webhook-signature",
            {
                "auth_algo": headers["paypal-auth-algo"],
                "cert_url": headers["paypal-cert-url"],
                "transmission_id": headers["paypal-transmission-id"],
                "transmission_sig": headers["paypal-transmission-sig"],
                "transmission_time": headers["paypal-transmission-time"],
                "webhook_id": settings.paypal_webhook_id,
                "webhook_event": event,
            },
        )
        if verification.get("verification_status") != "SUCCESS":
            raise PayPalSignatureError

    async def _apply_subscription_update(
        self,
        event: dict[str, Any],
        event_type: str,
    ) -> None:
        resource = event.get("resource")
        if not isinstance(resource, dict):
            raise PayPalWebhookPayloadError
        subscription_id = resource.get("id")
        if not isinstance(subscription_id, str) or not _PAYPAL_ID_PATTERN.fullmatch(
            subscription_id
        ):
            raise PayPalWebhookPayloadError
        subscription = await self.subscriptions.get_by_paypal_subscription_id(subscription_id)
        if subscription is None:
            raise PayPalWebhookPayloadError

        organization_id = resource.get("custom_id")
        if organization_id is not None and organization_id != subscription.organization_id:
            raise PayPalWebhookPayloadError
        event_time = _parse_timestamp(event.get("create_time"))
        if event_time is None:
            raise PayPalWebhookPayloadError
        if subscription.paypal_updated_at is not None and event_time <= (
            subscription.paypal_updated_at.replace(tzinfo=UTC)
            if subscription.paypal_updated_at.tzinfo is None
            else subscription.paypal_updated_at
        ):
            return

        billing_info = resource.get("billing_info")
        if billing_info is not None and not isinstance(billing_info, dict):
            raise PayPalWebhookPayloadError
        status_value = _status_for_event(event_type, resource.get("status"))
        if (
            status_value == "active"
            and isinstance(billing_info, dict)
            and _has_active_trial_cycle(billing_info)
        ):
            status_value = "trialing"
        subscription.status = status_value
        subscription.paypal_updated_at = event_time
        if isinstance(billing_info, dict):
            period_start = _nested_timestamp(billing_info, "last_payment", "time")
            period_end = _parse_timestamp(billing_info.get("next_billing_time"))
            if period_start is not None:
                subscription.current_period_start = period_start
            if period_end is not None:
                subscription.current_period_end = period_end
            subscription.trial_end = period_end if status_value == "trialing" else None
        subscriber = resource.get("subscriber")
        if isinstance(subscriber, dict):
            payer_id = subscriber.get("payer_id")
            if isinstance(payer_id, str):
                subscription.paypal_payer_id = payer_id
        subscription.updated_at = datetime.now(UTC)
        await record_audit_event(
            self.session,
            organization_id=subscription.organization_id,
            action="billing.subscription_updated",
            resource_type="subscription",
            resource_id=subscription.id,
            details={"status": status_value},
        )

    async def _paypal_request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        client_id, client_secret = self._require_api_configuration()
        base_url = settings.paypal_api_base_url.rstrip("/")
        try:
            async with httpx.AsyncClient(
                timeout=settings.provider_request_timeout_seconds,
            ) as client:
                token_response = await client.post(
                    f"{base_url}/v1/oauth2/token",
                    auth=(client_id, client_secret),
                    data={"grant_type": "client_credentials"},
                )
                token_response.raise_for_status()
                token_body: object = token_response.json()
                if not isinstance(token_body, dict):
                    raise PayPalUnavailableError
                access_token = token_body.get("access_token")
                if not isinstance(access_token, str) or not access_token:
                    raise PayPalUnavailableError

                request_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                }
                if request_id is not None:
                    request_headers["PayPal-Request-Id"] = request_id
                response = await client.request(
                    method,
                    f"{base_url}{path}",
                    json=payload,
                    headers=request_headers,
                )
                response.raise_for_status()
                if response.status_code == 204 or not response.content:
                    return {}
                body: object = response.json()
        except httpx.TimeoutException as error:
            logger.warning("paypal_request_timeout")
            raise PayPalUnavailableError from error
        except httpx.HTTPStatusError as error:
            logger.warning(
                "paypal_request_rejected",
                extra={"status_code": error.response.status_code},
            )
            raise PayPalUnavailableError from error
        except httpx.RequestError as error:
            logger.warning("paypal_request_failed", extra={"error_type": type(error).__name__})
            raise PayPalUnavailableError from error
        except json.JSONDecodeError as error:
            raise PayPalUnavailableError from error
        if not isinstance(body, dict):
            raise PayPalUnavailableError
        return body

    @staticmethod
    def _require_api_configuration() -> tuple[str, str]:
        client_id = settings.paypal_client_id.strip()
        client_secret = settings.paypal_client_secret.get_secret_value()
        if not client_id or not client_secret:
            raise PayPalUnavailableError
        return client_id, client_secret

    @staticmethod
    def _approval_url(body: dict[str, Any]) -> str | None:
        links = body.get("links")
        if not isinstance(links, list):
            return None
        for link in links:
            if not isinstance(link, dict) or link.get("rel") not in {"approve", "payer-action"}:
                continue
            href = link.get("href")
            if not isinstance(href, str):
                continue
            try:
                parsed = urlsplit(href)
                port = parsed.port
            except ValueError:
                continue
            hostname = parsed.hostname or ""
            if (
                parsed.scheme == "https"
                and parsed.username is None
                and parsed.password is None
                and port in {None, 443}
                and hostname
                in {
                    "paypal.com",
                    "www.paypal.com",
                    "sandbox.paypal.com",
                    "www.sandbox.paypal.com",
                }
            ):
                return href
        return None


InvalidStripeSignatureError = PayPalSignatureError
InvalidStripeEventError = PayPalWebhookPayloadError
BillingService = PayPalBillingService


def _status_for_event(event_type: str, resource_status: object) -> SubscriptionStatus:
    event_statuses: dict[str, SubscriptionStatus] = {
        "BILLING.SUBSCRIPTION.SUSPENDED": "past_due",
        "BILLING.SUBSCRIPTION.PAYMENT.FAILED": "past_due",
        "BILLING.SUBSCRIPTION.CANCELLED": "canceled",
        "BILLING.SUBSCRIPTION.EXPIRED": "canceled",
    }
    event_status = event_statuses.get(event_type)
    if event_status is not None:
        return event_status
    if isinstance(resource_status, str):
        resource_statuses: dict[str, SubscriptionStatus] = {
            "ACTIVE": "active",
            "APPROVAL_PENDING": "unpaid",
            "APPROVED": "unpaid",
            "SUSPENDED": "past_due",
            "CANCELLED": "canceled",
            "EXPIRED": "canceled",
        }
        return resource_statuses.get(resource_status.upper(), "unpaid")
    return "unpaid"


def _parse_timestamp(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise PayPalWebhookPayloadError
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise PayPalWebhookPayloadError from error
    if parsed.tzinfo is None:
        raise PayPalWebhookPayloadError
    return parsed.astimezone(UTC)


def _has_active_trial_cycle(billing_info: dict[str, Any]) -> bool:
    cycles = billing_info.get("cycle_executions")
    if cycles is None:
        return False
    if not isinstance(cycles, list):
        raise PayPalWebhookPayloadError
    for cycle in cycles:
        if not isinstance(cycle, dict):
            raise PayPalWebhookPayloadError
        if cycle.get("tenure_type") != "TRIAL":
            continue
        remaining = cycle.get("cycles_remaining")
        if isinstance(remaining, bool) or not isinstance(remaining, int):
            raise PayPalWebhookPayloadError
        if remaining > 0:
            return True
    return False


def _nested_timestamp(
    payload: dict[str, Any],
    parent_key: str,
    child_key: str,
) -> datetime | None:
    parent = payload.get(parent_key)
    if parent is None:
        return None
    if not isinstance(parent, dict):
        raise PayPalWebhookPayloadError
    return _parse_timestamp(parent.get(child_key))
