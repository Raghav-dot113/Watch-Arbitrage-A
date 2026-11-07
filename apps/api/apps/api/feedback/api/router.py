from __future__ import annotations

from apps.api.feedback.api.schemas import FeedbackRequest, FeedbackResponse
from apps.api.feedback.infrastructure.models import Feedback
from apps.api.feedback.infrastructure.repositories import FeedbackRepository
from apps.api.identity.api.context import OrganizationContext, get_organization_context
from apps.api.infrastructure.database import get_db
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])
_organization_context_dependency = Depends(get_organization_context)
_database_dependency = Depends(get_db)


@router.post(
    "",
    summary="Record opportunity feedback",
    description="Creates dealer feedback once per organization and idempotency key.",
    response_model=FeedbackResponse,
    responses={
        401: {"description": "Authentication or organization membership is required."},
        409: {"description": "The idempotency key conflicts with existing feedback."},
        422: {"description": "The feedback payload is invalid."},
    },
)
async def create_feedback(
    request: Request,
    payload: FeedbackRequest,
    context: OrganizationContext = _organization_context_dependency,
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    repository = FeedbackRepository(session)
    existing = await repository.get_by_idempotency_key(
        context.organization_id,
        payload.idempotency_key,
    )
    if existing is not None:
        return JSONResponse(
            status_code=200,
            content=FeedbackResponse.model_validate(existing).model_dump(mode="json"),
        )
    feedback = Feedback(
        id=generate_ulid("fbk"),
        organization_id=context.organization_id,
        user_id=context.user_id,
        opportunity_id=payload.opportunity_id,
        decision=payload.decision,
        notes=payload.notes,
        idempotency_key=payload.idempotency_key,
    )
    await repository.save(feedback)
    await session.commit()
    return JSONResponse(
        status_code=201,
        content=FeedbackResponse.model_validate(feedback).model_dump(mode="json"),
    )
