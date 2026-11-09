from __future__ import annotations

from typing import Annotated

from apps.api.billing.api.schemas import (
    PayPalCheckoutRequest,
    PayPalSubscriptionApprovalResponse,
    PayPalWebhookResponse,
    SubscriptionResponse,
)
from apps.api.billing.application.service import (
    MAX_PAYPAL_WEBHOOK_BODY_BYTES,
    PayPalBillingService,
    PayPalOrganizationNotFoundError,
    PayPalPlanNotConfiguredError,
    PayPalSignatureError,
    PayPalSubscriptionConflictError,
    PayPalSubscriptionNotFoundError,
    PayPalUnavailableError,
    PayPalWebhookPayloadError,
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
    subscription = await PayPalBillingService(session).get_subscription(_organization_id(actor))
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
    response_model=SuccessEnvelope[PayPalSubscriptionApprovalResponse],
)
async def create_checkout_session(
    payload: PayPalCheckoutRequest,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.BILLING_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=255)],
) -> dict[str, object]:
    try:
        body = await PayPalBillingService(session).create_checkout_session(
            _organization_id(actor),
            actor.email,
            payload.plan_id,
            user_id=actor.user_id,
            idempotency_key=idempotency_key,
            trace_id=request.state.trace_id,
        )
    except PayPalPlanNotConfiguredError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Requested subscription plan is not configured",
        ) from error
    except PayPalOrganizationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        ) from error
    except PayPalSubscriptionConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization already has a subscription requiring action",
        ) from error
    except PayPalUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PayPal billing is not available",
        ) from error
    return success_response(request, PayPalSubscriptionApprovalResponse.model_validate(body))


@router.post(
    "/cancel",
    response_model=SuccessEnvelope[SubscriptionResponse],
)
async def cancel_subscription(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.BILLING_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=255)],
) -> dict[str, object]:
    try:
        subscription = await PayPalBillingService(session).cancel_subscription(
            _organization_id(actor),
            actor.user_id,
            idempotency_key,
            trace_id=request.state.trace_id,
        )
    except PayPalSubscriptionNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization does not have a PayPal subscription",
        ) from error
    except PayPalUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PayPal billing is not available",
        ) from error
    body = SubscriptionResponse.model_validate(subscription)
    return success_response(request, body)


@router.post(
    "/webhook",
    response_model=PayPalWebhookResponse,
)
async def paypal_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    paypal_auth_algo: Annotated[
        str | None, Header(alias="PayPal-Auth-Algo", max_length=128)
    ] = None,
    paypal_cert_url: Annotated[str | None, Header(alias="PayPal-Cert-Url", max_length=2048)] = None,
    paypal_transmission_id: Annotated[
        str | None, Header(alias="PayPal-Transmission-Id", max_length=256)
    ] = None,
    paypal_transmission_sig: Annotated[
        str | None, Header(alias="PayPal-Transmission-Sig", max_length=2048)
    ] = None,
    paypal_transmission_time: Annotated[
        str | None, Header(alias="PayPal-Transmission-Time", max_length=128)
    ] = None,
) -> PayPalWebhookResponse:
    content_length = request.headers.get("content-length")
    if (
        content_length is not None
        and content_length.isdigit()
        and int(content_length) > MAX_PAYPAL_WEBHOOK_BODY_BYTES
    ):
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="PayPal webhook payload is too large",
        )
    headers = {
        "paypal-auth-algo": paypal_auth_algo or "",
        "paypal-cert-url": paypal_cert_url or "",
        "paypal-transmission-id": paypal_transmission_id or "",
        "paypal-transmission-sig": paypal_transmission_sig or "",
        "paypal-transmission-time": paypal_transmission_time or "",
    }
    try:
        created = await PayPalBillingService(session).process_webhook(
            await _read_webhook_body(request),
            headers,
        )
    except PayPalSignatureError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PayPal webhook signature is invalid",
        ) from error
    except PayPalWebhookPayloadError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PayPal webhook payload is invalid",
        ) from error
    except PayPalUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PayPal webhook verification is not available",
        ) from error
    return PayPalWebhookResponse(duplicate=not created)


async def _read_webhook_body(request: Request) -> bytes:
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_PAYPAL_WEBHOOK_BODY_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="PayPal webhook payload is too large",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _organization_id(actor: AuthContext) -> str:
    if actor.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return actor.organization_id
