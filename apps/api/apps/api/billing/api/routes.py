from __future__ import annotations

from typing import Annotated

from apps.api.billing.api.schemas import (
    StripeCheckoutRequest,
    StripePortalResponse,
    StripeSessionResponse,
    StripeWebhookResponse,
    SubscriptionResponse,
)
from apps.api.billing.application.service import (
    MAX_STRIPE_WEBHOOK_BODY_BYTES,
    StripeBillingService,
    StripeCustomerNotFoundError,
    StripePlanNotConfiguredError,
    StripeSignatureError,
    StripeUnavailableError,
    StripeWebhookPayloadError,
)
from apps.api.identity.api.auth import AuthContext, Permission, require_permissions
from apps.api.infrastructure.api_response import SuccessEnvelope, success_response
from apps.api.infrastructure.database import get_db
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.get(
    "/subscription",
    response_model=SuccessEnvelope[SubscriptionResponse],
)
async def get_subscription(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    subscription = await StripeBillingService(session).get_subscription(_organization_id(actor))
    body = SubscriptionResponse(
        id=subscription.id if subscription is not None else None,
        status=subscription.status if subscription is not None else "unpaid",
        plan_id=subscription.plan_id if subscription is not None else None,
        current_period_start=subscription.current_period_start if subscription else None,
        current_period_end=subscription.current_period_end if subscription else None,
        trial_end=subscription.trial_end if subscription else None,
    )
    return success_response(request, body)


@router.post(
    "/checkout",
    response_model=SuccessEnvelope[StripeSessionResponse],
)
async def create_checkout_session(
    payload: StripeCheckoutRequest,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.BILLING_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        body = await StripeBillingService(session).create_checkout_session(
            _organization_id(actor),
            actor.email,
            payload.plan_id,
            user_id=actor.user_id,
            trace_id=request.state.trace_id,
        )
    except StripePlanNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Requested subscription plan is not configured",
        ) from error
    except StripeUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe billing is not available",
        ) from error
    return success_response(request, StripeSessionResponse.model_validate(body))


@router.post(
    "/portal",
    response_model=SuccessEnvelope[StripePortalResponse],
)
async def create_portal_session(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.BILLING_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        body = await StripeBillingService(session).create_portal_session(
            _organization_id(actor),
            actor.user_id,
            trace_id=request.state.trace_id,
        )
    except StripeCustomerNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization does not have a Stripe customer",
        ) from error
    except StripeUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe billing is not available",
        ) from error
    return success_response(request, StripePortalResponse.model_validate(body))


@router.post(
    "/webhook",
    response_model=StripeWebhookResponse,
)
async def stripe_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    stripe_signature: Annotated[
        str | None, Header(alias="Stripe-Signature", max_length=1024)
    ] = None,
) -> StripeWebhookResponse:
    if stripe_signature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe-Signature header is required",
        )
    content_length = request.headers.get("content-length")
    if (
        content_length is not None
        and content_length.isdigit()
        and int(content_length) > MAX_STRIPE_WEBHOOK_BODY_BYTES
    ):
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Stripe webhook payload is too large",
        )
    try:
        created = await StripeBillingService(session).process_webhook(
            await _read_webhook_body(request),
            stripe_signature,
        )
    except StripeSignatureError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe webhook signature is invalid or expired",
        ) from error
    except StripeWebhookPayloadError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe webhook payload is invalid",
        ) from error
    except StripeUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook verification is not configured",
        ) from error
    return StripeWebhookResponse(duplicate=not created)


async def _read_webhook_body(request: Request) -> bytes:
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_STRIPE_WEBHOOK_BODY_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="Stripe webhook payload is too large",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _organization_id(actor: AuthContext) -> str:
    if actor.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return actor.organization_id
