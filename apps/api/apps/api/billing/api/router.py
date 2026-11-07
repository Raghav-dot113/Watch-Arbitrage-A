from __future__ import annotations

import hashlib
import hmac
import time

from apps.api.billing.api.schemas import StripeWebhookResponse
from apps.api.billing.infrastructure.models import StripeWebhookEvent
from apps.api.infrastructure.database import get_db
from apps.api.settings import settings
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
_database_dependency = Depends(get_db)


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
    if abs(int(time.time()) - timestamp_value) > 300:
        return False
    signed_payload = timestamp.encode("ascii") + b"." + payload
    expected = hmac.new(
        settings.stripe_webhook_secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


class StripeEvent(BaseModel):
    id: str
    type: str
    data: dict[str, object]


@router.post(
    "/stripe/webhook",
    summary="Receive Stripe webhook",
    description="Verifies and processes an idempotent Stripe event.",
    response_model=StripeWebhookResponse,
    responses={
        401: {"description": "The Stripe signature is missing or invalid."},
        409: {"description": "The Stripe event conflicts with existing state."},
        422: {"description": "The webhook payload is invalid."},
    },
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    payload = await request.body()
    if not verify_stripe_signature(payload, stripe_signature):
        return JSONResponse(
            status_code=401,
            content={
                "error": {"code": "UNAUTHORIZED", "message": "Invalid Stripe webhook signature"}
            },
        )
    try:
        event = StripeEvent.model_validate_json(payload)
    except Exception:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "VALIDATION_ERROR", "message": "Invalid Stripe event"}},
        )
    existing = await session.scalar(
        select(StripeWebhookEvent).where(StripeWebhookEvent.provider_event_id == event.id)
    )
    replayed = existing is not None
    if not replayed:
        from chronoarb.domain.ulid import generate_ulid

        session.add(
            StripeWebhookEvent(
                id=generate_ulid("str"),
                provider_event_id=event.id,
                event_type=event.type,
            )
        )
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            replayed = True
    response = StripeWebhookResponse(received=True, event_id=event.id, replayed=replayed)
    return JSONResponse(content=response.model_dump(mode="json"))
