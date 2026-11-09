from __future__ import annotations

from apps.api.feedback.api.schemas import FeedbackRequest, FeedbackResponse, LegacyFeedbackRequest
from apps.api.feedback.application.service import FeedbackService, OpportunityNotFoundError
from apps.api.idempotency.application.service import IdempotencyKeyReuseError
from apps.api.identity.api.context import OrganizationContext
from apps.api.identity.api.permissions import require_permission
from apps.api.infrastructure.database import get_db
from apps.api.responses import success_response
from apps.api.schemas import ApiErrorResponse, ApiSuccessEnvelope
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["feedback"])
_write_permission_dependency = Depends(require_permission("feedback:write"))
_database_dependency = Depends(get_db)


async def _submit_feedback(
    *,
    request: Request,
    opportunity_id: str,
    payload: FeedbackRequest,
    idempotency_key: str,
    context: OrganizationContext,
    session: AsyncSession,
) -> JSONResponse:
    try:
        result = await FeedbackService(session).create(
            organization_id=context.organization_id,
            user_id=context.user_id,
            opportunity_id=opportunity_id,
            idempotency_key=idempotency_key,
            request=payload,
        )
    except IdempotencyKeyReuseError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "The idempotency key was already used with a different request.",
                "field_errors": {"Idempotency-Key": ["Use a new key for a different request."]},
            },
        ) from exc
    except OpportunityNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Opportunity not found") from exc
    return success_response(
        result.response_body,
        getattr(request.state, "trace_id", "unknown"),
        status_code=result.status_code,
    )


@router.post(
    "/api/v1/opportunities/{opp_id}/feedback",
    summary="Record opportunity feedback",
    description="Records a tenant-scoped opportunity decision idempotently.",
    response_model=ApiSuccessEnvelope[FeedbackResponse],
    status_code=201,
    responses={
        401: {"model": ApiErrorResponse, "description": "Authentication is required."},
        403: {"model": ApiErrorResponse, "description": "The role cannot record feedback."},
        404: {"model": ApiErrorResponse, "description": "The opportunity is not available."},
        200: {"model": ApiSuccessEnvelope[FeedbackResponse], "description": "Idempotent replay."},
        409: {
            "model": ApiErrorResponse,
            "description": "The request conflicts with current state.",
        },
        422: {
            "model": ApiErrorResponse,
            "description": "The payload or idempotency key is invalid.",
        },
    },
)
async def create_opportunity_feedback(
    request: Request,
    opp_id: str,
    payload: FeedbackRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    context: OrganizationContext = _write_permission_dependency,
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    return await _submit_feedback(
        request=request,
        opportunity_id=opp_id,
        payload=payload,
        idempotency_key=idempotency_key,
        context=context,
        session=session,
    )


@router.post(
    "/api/v1/feedback",
    summary="Record opportunity feedback (deprecated)",
    description="Deprecated alias for `/api/v1/opportunities/{opp_id}/feedback`.",
    response_model=ApiSuccessEnvelope[FeedbackResponse],
    status_code=201,
    deprecated=True,
    responses={
        401: {"model": ApiErrorResponse, "description": "Authentication is required."},
        403: {"model": ApiErrorResponse, "description": "The role cannot record feedback."},
        404: {"model": ApiErrorResponse, "description": "The opportunity is not available."},
        200: {"model": ApiSuccessEnvelope[FeedbackResponse], "description": "Idempotent replay."},
        422: {
            "model": ApiErrorResponse,
            "description": "The payload or idempotency key is invalid.",
        },
    },
)
async def create_feedback_legacy(
    request: Request,
    payload: LegacyFeedbackRequest,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        min_length=1,
        max_length=128,
    ),
    context: OrganizationContext = _write_permission_dependency,
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    key = idempotency_key or payload.idempotency_key
    if key is None:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "An Idempotency-Key header is required.",
                "field_errors": {"Idempotency-Key": ["This header is required."]},
            },
        )
    return await _submit_feedback(
        request=request,
        opportunity_id=payload.opportunity_id,
        payload=FeedbackRequest(decision=payload.decision, notes=payload.notes),
        idempotency_key=key,
        context=context,
        session=session,
    )
