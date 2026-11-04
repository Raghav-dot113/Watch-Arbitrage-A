from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

import httpx
from apps.api.billing.infrastructure.models import Subscription
from apps.api.billing.infrastructure.repositories import (
    StripeWebhookEventRepository,
    SubscriptionRepository,
)
from apps.api.identity.infrastructure.models import Organization
from apps.api.integrations.infrastructure.models import StripeWebhookEvent
from apps.api.operations.application.audit import record_audit_event
from apps.api.settings import settings
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid

logger = logging.getLogger(__name__)
_WEBHOOK_TOLERANCE_SECONDS = 300
MAX_STRIPE_WEBHOOK_BODY_BYTES = 1_000_000
_SUBSCRIPTION_EVENTS = {
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}


class StripeUnavailableError(Exception):
    pass


class StripePlanNotConfiguredError(Exception):
    pass


class StripeCustomerNotFoundError(Exception):
    pass


class StripeSignatureError(Exception):
    pass


class StripeWebhookPayloadError(Exception):
    pass


def verify_stripe_signature(
    payload: bytes,
    signature_header: str,
    secret: str,
    *,
    now: int | None = None,
) -> None:
    timestamp: int | None = None
    signatures: list[str] = []
    for part in signature_header.split(","):
        key, separator, value = part.strip().partition("=")
        if not separator:
            continue
        if key == "t" and timestamp is None:
            try:
                timestamp = int(value)
            except ValueError:
                raise StripeSignatureError from None
        elif key == "v1":
            signatures.append(value)
    current_time = int(time.time()) if now is None else now
    if timestamp is None or abs(current_time - timestamp) > _WEBHOOK_TOLERANCE_SECONDS:
        raise StripeSignatureError
    signed_payload = str(timestamp).encode("ascii") + b"." + payload
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, candidate) for candidate in signatures):
        raise StripeSignatureError


class StripeBillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.subscriptions = SubscriptionRepository(session)
        self.events = StripeWebhookEventRepository(session)

    async def get_subscription(self, organization_id: str) -> Subscription | None:
        return await self.subscriptions.get_latest_for_org(organization_id)

    async def create_checkout_session(
        self,
        organization_id: str,
        user_email: str,
        plan_id: str,
        *,
        user_id: str,
        trace_id: str,
    ) -> dict[str, str]:
        price_id = settings.stripe_price_ids.get(plan_id)
        if not price_id:
            raise StripePlanNotConfiguredError
        self._require_api_key()
        current = await self.subscriptions.get_latest_for_org(organization_id)
        form_data = {
            "mode": "subscription",
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": "1",
            "success_url": settings.stripe_success_url,
            "cancel_url": settings.stripe_cancel_url,
            "client_reference_id": organization_id,
            "metadata[organization_id]": organization_id,
            "metadata[plan_id]": plan_id,
            "subscription_data[metadata][organization_id]": organization_id,
            "subscription_data[metadata][plan_id]": plan_id,
        }
        if current is not None and current.stripe_customer_id is not None:
            form_data["customer"] = current.stripe_customer_id
        else:
            form_data["customer_email"] = user_email
        body = await self._stripe_post("/v1/checkout/sessions", form_data)
        session_id = body.get("id")
        checkout_url = body.get("url")
        if not isinstance(session_id, str) or not isinstance(checkout_url, str):
            raise StripeUnavailableError
        self._validate_stripe_redirect(checkout_url)
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="billing.checkout_session_created",
            resource_type="subscription",
            resource_id=organization_id,
            details={"plan_id": plan_id, "checkout_session_id": session_id},
            trace_id=trace_id,
        )
        await self.session.commit()
        return {"session_id": session_id, "url": checkout_url}

    async def create_portal_session(
        self,
        organization_id: str,
        user_id: str,
        *,
        trace_id: str,
    ) -> dict[str, str]:
        self._require_api_key()
        current = await self.subscriptions.get_latest_for_org(organization_id)
        if current is None or current.stripe_customer_id is None:
            raise StripeCustomerNotFoundError
        body = await self._stripe_post(
            "/v1/billing_portal/sessions",
            {
                "customer": current.stripe_customer_id,
                "return_url": settings.stripe_portal_return_url,
            },
        )
        portal_url = body.get("url")
        if not isinstance(portal_url, str):
            raise StripeUnavailableError
        self._validate_stripe_redirect(portal_url)
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="billing.portal_session_created",
            resource_type="subscription",
            resource_id=organization_id,
            trace_id=trace_id,
        )
        await self.session.commit()
        return {"url": portal_url}

    async def process_webhook(self, payload: bytes, signature_header: str) -> bool:
        secret = settings.stripe_webhook_secret.get_secret_value()
        if not secret:
            raise StripeUnavailableError
        if len(payload) > MAX_STRIPE_WEBHOOK_BODY_BYTES:
            raise StripeWebhookPayloadError
        verify_stripe_signature(payload, signature_header, secret)
        try:
            event: object = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise StripeWebhookPayloadError from error
        if not isinstance(event, dict):
            raise StripeWebhookPayloadError
        event_id = event.get("id")
        event_type = event.get("type")
        if not isinstance(event_id, str) or not event_id or not isinstance(event_type, str):
            raise StripeWebhookPayloadError
        if await self.events.get_by_id(event_id) is not None:
            return False

        mutation: tuple[str, str, dict[str, Any]] | None = None
        if event_type in _SUBSCRIPTION_EVENTS:
            mutation = self._subscription_mutation(event, event_type)

        try:
            if mutation is not None:
                organization_id, userless_action, subscription_data = mutation
                await self._apply_subscription_update(
                    organization_id,
                    userless_action,
                    subscription_data,
                )
            self.session.add(
                StripeWebhookEvent(
                    id=event_id,
                    event_type=event_type,
                )
            )
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            if await self.events.get_by_id(event_id) is not None:
                return False
            raise
        return True

    @staticmethod
    def _subscription_mutation(
        event: dict[str, Any],
        event_type: str,
    ) -> tuple[str, str, dict[str, Any]]:
        data = event.get("data")
        obj = data.get("object") if isinstance(data, dict) else None
        if not isinstance(obj, dict):
            raise StripeWebhookPayloadError
        metadata = obj.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        organization_id = metadata.get("organization_id") or obj.get("client_reference_id")
        stripe_subscription_id = obj.get("id")
        customer_id = obj.get("customer")
        if not isinstance(organization_id, str) or not organization_id:
            raise StripeWebhookPayloadError
        if not isinstance(stripe_subscription_id, str) or not stripe_subscription_id:
            raise StripeWebhookPayloadError
        if customer_id is not None and not isinstance(customer_id, str):
            raise StripeWebhookPayloadError
        status_value = "canceled" if event_type.endswith(".deleted") else obj.get("status")
        normalized_status = _normalize_subscription_status(status_value)
        subscription_data: dict[str, Any] = {
            "stripe_customer_id": customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "status": normalized_status,
            "plan_id": metadata.get("plan_id")
            if isinstance(metadata.get("plan_id"), str)
            else None,
            "current_period_start": _timestamp(obj.get("current_period_start")),
            "current_period_end": _timestamp(obj.get("current_period_end")),
            "trial_end": _timestamp(obj.get("trial_end")),
        }
        return organization_id, "billing.subscription_updated", subscription_data

    async def _apply_subscription_update(
        self,
        organization_id: str,
        action: str,
        subscription_data: dict[str, Any],
    ) -> None:
        org_result = await self.session.execute(
            select(Organization)
            .where(Organization.id == organization_id)
            .with_for_update(of=Organization)
        )
        if org_result.scalar_one_or_none() is None:
            raise StripeWebhookPayloadError
        existing = await self.subscriptions.get_by_stripe_subscription_id(
            subscription_data["stripe_subscription_id"]
        )
        if existing is None:
            existing = Subscription(
                id=generate_ulid("sub"),
                organization_id=organization_id,
                status=subscription_data["status"],
                stripe_customer_id=subscription_data["stripe_customer_id"],
                stripe_subscription_id=subscription_data["stripe_subscription_id"],
                plan_id=subscription_data["plan_id"],
                current_period_start=subscription_data["current_period_start"],
                current_period_end=subscription_data["current_period_end"],
                trial_end=subscription_data["trial_end"],
            )
            self.session.add(existing)
        elif existing.organization_id != organization_id:
            raise StripeWebhookPayloadError
        else:
            for name, value in subscription_data.items():
                setattr(existing, name, value)
            existing.updated_at = datetime.now(UTC)
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            action=action,
            resource_type="subscription",
            resource_id=existing.id,
            details={"status": subscription_data["status"]},
        )

    async def _stripe_post(self, path: str, form_data: dict[str, str]) -> dict[str, Any]:
        key = self._require_api_key()
        url = f"{settings.stripe_api_base_url.rstrip('/')}{path}"
        try:
            async with httpx.AsyncClient(
                timeout=settings.provider_request_timeout_seconds
            ) as client:
                response = await client.post(
                    url,
                    data=form_data,
                    headers={"Authorization": f"Bearer {key}"},
                )
                response.raise_for_status()
                body: object = response.json()
        except httpx.TimeoutException as error:
            logger.warning("stripe_request_timeout")
            raise StripeUnavailableError from error
        except httpx.RequestError as error:
            logger.warning("stripe_request_failed", extra={"error_type": type(error).__name__})
            raise StripeUnavailableError from error
        except httpx.HTTPStatusError as error:
            logger.warning(
                "stripe_request_rejected",
                extra={"status_code": error.response.status_code},
            )
            raise StripeUnavailableError from error
        except json.JSONDecodeError as error:
            raise StripeUnavailableError from error
        if not isinstance(body, dict):
            raise StripeUnavailableError
        return body

    @staticmethod
    def _require_api_key() -> str:
        key = settings.stripe_secret_key.get_secret_value()
        if not key:
            raise StripeUnavailableError
        return key

    @staticmethod
    def _validate_stripe_redirect(value: str) -> None:
        try:
            parsed = urlsplit(value)
        except ValueError as error:
            raise StripeUnavailableError from error
        hostname = parsed.hostname or ""
        if (
            parsed.scheme != "https"
            or parsed.username is not None
            or parsed.password is not None
            or not (hostname == "stripe.com" or hostname.endswith(".stripe.com"))
        ):
            raise StripeUnavailableError


def _normalize_subscription_status(value: object) -> str:
    if isinstance(value, str) and value in {
        "trialing",
        "active",
        "past_due",
        "canceled",
        "unpaid",
    }:
        return str(value)
    return "unpaid"


def _timestamp(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise StripeWebhookPayloadError
    try:
        return datetime.fromtimestamp(value, tz=UTC)
    except (OverflowError, OSError, ValueError) as error:
        raise StripeWebhookPayloadError from error
