from __future__ import annotations

from apps.api.billing.api.schemas import StripeWebhookResponse
from apps.api.billing.application.service import (
    BillingService,
    InvalidStripeEventError,
    InvalidStripeSignatureError,
)
from apps.api.billing.application.service import (
    verify_stripe_signature as verify_stripe_signature,
)
from apps.api.infrastructure.database import get_db
from apps.api.responses import success_response
from apps.api.schemas import ApiErrorResponse, ApiSuccessEnvelope
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
_database_dependency = Depends(get_db)


@router.post(
    "/webhook",
    summary="Receive Stripe webhook",
    description="Verifies and records an idempotent Stripe event.",
    response_model=ApiSuccessEnvelope[StripeWebhookResponse],
    responses={
        401: {
            "model": ApiErrorResponse,
            "description": "The Stripe signature is missing or invalid.",
        },
        422: {"model": ApiErrorResponse, "description": "The webhook payload is invalid."},
    },
)
@router.post(
    "/stripe/webhook",
    summary="Receive Stripe webhook (deprecated)",
    description="Deprecated alias for `/api/v1/billing/webhook`.",
    response_model=ApiSuccessEnvelope[StripeWebhookResponse],
    deprecated=True,
    responses={
        401: {
            "model": ApiErrorResponse,
            "description": "The Stripe signature is missing or invalid.",
        },
        422: {"model": ApiErrorResponse, "description": "The webhook payload is invalid."},
    },
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    try:
        result = await BillingService(session).receive_webhook(
            await request.body(),
            stripe_signature,
        )
    except InvalidStripeSignatureError as exc:
        raise HTTPException(
            status_code=401,
            detail="The Stripe signature is missing or invalid.",
        ) from exc
    except InvalidStripeEventError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "The webhook payload is invalid.",
                "field_errors": {"body": ["Invalid Stripe event."]},
            },
        ) from exc
    return success_response(result, getattr(request.state, "trace_id", "unknown"))
