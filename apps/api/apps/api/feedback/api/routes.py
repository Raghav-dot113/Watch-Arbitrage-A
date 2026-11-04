from __future__ import annotations

from typing import Annotated

from apps.api.feedback.api.schemas import (
    ActivityItemResponse,
    FeedbackCreateRequest,
    FeedbackCreateResponse,
    FeedbackResponse,
    OpportunityHistoryItemResponse,
    TradeOutcomeCreateRequest,
    TradeOutcomeResponse,
)
from apps.api.feedback.application.service import (
    FeedbackService,
    IdempotencyConflictError,
    OpportunityNotFoundError,
    TradeOutcomeStateError,
)
from apps.api.feedback.infrastructure.models import TradeOutcome
from apps.api.identity.api.auth import AuthContext, Permission, require_permissions
from apps.api.infrastructure.api_response import SuccessEnvelope, success_response
from apps.api.infrastructure.database import get_db
from apps.api.infrastructure.idempotency import require_idempotency_key
from apps.api.opportunities.domain.state_machine import InvalidOpportunityTransitionError
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])
activity_router = APIRouter(prefix="/api/v1/activity", tags=["activity"])


@router.post(
    "/{opportunity_id}/feedback",
    response_model=SuccessEnvelope[FeedbackCreateResponse],
)
async def record_feedback(
    opportunity_id: str,
    payload: FeedbackCreateRequest,
    request: Request,
    http_response: Response,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.FEEDBACK_WRITE))],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> dict[str, object]:
    organization_id = _organization_id(actor)
    try:
        result = await FeedbackService(session).record_feedback(
            opportunity_id,
            organization_id,
            actor.user_id,
            idempotency_key,
            payload,
            trace_id=request.state.trace_id,
        )
    except OpportunityNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    except (IdempotencyConflictError, InvalidOpportunityTransitionError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback conflicts with the opportunity's current state or prior request",
        ) from error
    body = FeedbackCreateResponse(
        feedback=FeedbackResponse.model_validate(result.feedback),
        opportunity_state=result.opportunity_state,
    )
    if result.created:
        http_response.status_code = status.HTTP_201_CREATED
    return success_response(request, body)


@router.get(
    "/{opportunity_id}/history",
    response_model=SuccessEnvelope[list[OpportunityHistoryItemResponse]],
)
async def get_opportunity_history(
    opportunity_id: str,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        versions = await FeedbackService(session).list_history(
            opportunity_id,
            _organization_id(actor),
        )
    except OpportunityNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    return success_response(
        request,
        [OpportunityHistoryItemResponse.model_validate(version) for version in versions],
    )


@router.post(
    "/{opportunity_id}/trade-outcome",
    response_model=SuccessEnvelope[TradeOutcomeResponse],
)
async def record_trade_outcome(
    opportunity_id: str,
    payload: TradeOutcomeCreateRequest,
    request: Request,
    http_response: Response,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OUTCOMES_WRITE))],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> dict[str, object]:
    try:
        result = await FeedbackService(session).record_trade_outcome(
            opportunity_id,
            _organization_id(actor),
            actor.user_id,
            idempotency_key,
            payload,
            trace_id=request.state.trace_id,
        )
    except OpportunityNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    except (IdempotencyConflictError, TradeOutcomeStateError) as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trade outcome conflicts with the opportunity's state or prior request",
        ) from error
    body = _trade_outcome_response(result.outcome)
    if result.created:
        http_response.status_code = status.HTTP_201_CREATED
    return success_response(request, body)


@activity_router.get(
    "",
    response_model=SuccessEnvelope[list[ActivityItemResponse]],
    response_model_exclude_none=True,
)
async def list_activity(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    entries = await FeedbackService(session).list_activity(
        _organization_id(actor),
        limit=limit,
    )
    return success_response(
        request,
        [ActivityItemResponse.model_validate(entry) for entry in entries],
    )


@activity_router.get(
    "/outcomes",
    response_model=SuccessEnvelope[list[TradeOutcomeResponse]],
    response_model_exclude_none=True,
)
async def list_trade_outcomes(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    outcomes = await FeedbackService(session).list_outcomes(
        _organization_id(actor),
        limit=limit,
    )
    return success_response(
        request,
        [_trade_outcome_response(outcome) for outcome in outcomes],
    )


def _trade_outcome_response(outcome: TradeOutcome) -> TradeOutcomeResponse:
    return TradeOutcomeResponse(
        id=outcome.id,
        organization_id=outcome.organization_id,
        user_id=outcome.user_id,
        opportunity_id=outcome.opportunity_id,
        reference_id=outcome.reference_id,
        acquisition_price=outcome.acquisition_price,
        acquisition_currency=outcome.acquisition_currency,
        resale_price=outcome.resale_price,
        resale_currency=outcome.resale_currency,
        actual_profit=outcome.actual_profit,
        actual_profit_currency=(
            outcome.acquisition_currency if outcome.actual_profit is not None else None
        ),
        days_to_sell=outcome.days_to_sell,
        created_at=outcome.created_at,
    )


def _organization_id(actor: AuthContext) -> str:
    if actor.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return actor.organization_id
