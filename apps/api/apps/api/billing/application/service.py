from __future__ import annotations

import hashlib
import hmac
import time

from apps.api.billing.api.schemas import StripeEvent, StripeWebhookResponse
from apps.api.billing.infrastructure.models import StripeWebhookEvent
from apps.api.settings import settings
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid

STRIPE_WEBHOOK_TOLERANCE_SECONDS = 300


class InvalidStripeSignatureError(Exception):
    pass


class InvalidStripeEventError(Exception):
    pass


def verify_stripe_signature(payload: bytes, signature_header: str | None) -> bool:
    if not settings.stripe_webhook_secret or not signature_header:
        return False
    parts = dict(item.split("=", 1) for item in signature_header.split(",") if "=" in item)
    timestamp = parts.get("t")
    signature = parts.get("v1")
    if timestamp is None or signature is None:
        return False
    try:
        timestamp_value = int(timestamp)
    except ValueError:
        return False
    if abs(int(time.time()) - timestamp_value) > STRIPE_WEBHOOK_TOLERANCE_SECONDS:
        return False
    signed_payload = timestamp.encode("ascii") + b"." + payload
    expected = hmac.new(
        settings.stripe_webhook_secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def receive_webhook(
        self,
        payload: bytes,
        signature_header: str | None,
    ) -> StripeWebhookResponse:
        if not verify_stripe_signature(payload, signature_header):
            raise InvalidStripeSignatureError
        try:
            event = StripeEvent.model_validate_json(payload)
        except ValidationError as exc:
            raise InvalidStripeEventError from exc

        statement = select(StripeWebhookEvent).where(
            StripeWebhookEvent.provider_event_id == event.id
        )
        existing = await self._session.scalar(statement)
        if existing is not None:
            return StripeWebhookResponse(
                received=True,
                event_id=event.id,
                replayed=True,
            )

        self._session.add(
            StripeWebhookEvent(
                id=generate_ulid("str"),
                provider_event_id=event.id,
                event_type=event.type,
            )
        )
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            existing = await self._session.scalar(statement)
            if existing is None:
                raise
            return StripeWebhookResponse(
                received=True,
                event_id=event.id,
                replayed=True,
            )

        return StripeWebhookResponse(
            received=True,
            event_id=event.id,
            replayed=False,
        )
