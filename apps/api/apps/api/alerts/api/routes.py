from __future__ import annotations

from typing import Annotated

from apps.api.alerts.api.schemas import (
    AlertDeliveryResponse,
    AlertRuleCreateRequest,
    AlertRuleResponse,
    AlertTestAcceptedResponse,
    DeliveryStatus,
)
from apps.api.alerts.application.service import (
    AlertRuleDisabledError,
    AlertRuleNotFoundError,
    AlertService,
    AlertTestIdempotencyConflictError,
)
from apps.api.identity.api.auth import AuthContext, Permission, require_permissions
from apps.api.infrastructure.api_response import SuccessEnvelope, success_response
from apps.api.infrastructure.database import get_db
from apps.api.infrastructure.idempotency import require_idempotency_key
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get(
    "/rules",
    response_model=SuccessEnvelope[list[AlertRuleResponse]],
    response_model_exclude_none=True,
)
async def list_alert_rules(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    rules = await AlertService(session).list_rules(_organization_id(actor), limit=limit)
    return success_response(request, [AlertRuleResponse.model_validate(rule) for rule in rules])


@router.post(
    "/rules",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[AlertRuleResponse],
    response_model_exclude_none=True,
)
async def create_alert_rule(
    payload: AlertRuleCreateRequest,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.ALERTS_CREATE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    rule = await AlertService(session).create_rule(
        _organization_id(actor),
        actor.user_id,
        payload,
        trace_id=request.state.trace_id,
    )
    return success_response(request, AlertRuleResponse.model_validate(rule))


@router.get(
    "/rules/{rule_id}",
    response_model=SuccessEnvelope[AlertRuleResponse],
    response_model_exclude_none=True,
)
async def get_alert_rule(
    rule_id: str,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    rule = await AlertService(session).get_rule(_organization_id(actor), rule_id)
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return success_response(request, AlertRuleResponse.model_validate(rule))


@router.put(
    "/rules/{rule_id}",
    response_model=SuccessEnvelope[AlertRuleResponse],
    response_model_exclude_none=True,
)
async def update_alert_rule(
    rule_id: str,
    payload: AlertRuleCreateRequest,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.ALERTS_CREATE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        rule = await AlertService(session).update_rule(
            _organization_id(actor),
            actor.user_id,
            rule_id,
            payload,
            trace_id=request.state.trace_id,
        )
    except AlertRuleNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    return success_response(request, AlertRuleResponse.model_validate(rule))


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: str,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.ALERTS_CREATE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await AlertService(session).disable_rule(
            _organization_id(actor),
            actor.user_id,
            rule_id,
            trace_id=request.state.trace_id,
        )
    except AlertRuleNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/rules/{rule_id}/test",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessEnvelope[AlertTestAcceptedResponse],
)
async def request_alert_test(
    rule_id: str,
    request: Request,
    http_response: Response,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.ALERTS_CREATE))],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> dict[str, object]:
    try:
        result = await AlertService(session).request_test_notification(
            _organization_id(actor),
            actor.user_id,
            rule_id,
            idempotency_key,
            trace_id=request.state.trace_id,
        )
    except AlertRuleNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    except AlertRuleDisabledError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Disabled alert rules cannot send test notifications",
        ) from error
    except AlertTestIdempotencyConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key was already used with a different request",
        ) from error
    if not result.created:
        http_response.status_code = status.HTTP_200_OK
    body = AlertTestAcceptedResponse(event_id=result.event_id, status="pending")
    return success_response(request, body)


@router.get(
    "/deliveries",
    response_model=SuccessEnvelope[list[AlertDeliveryResponse]],
    response_model_exclude_none=True,
)
async def list_alert_deliveries(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
    rule_id: Annotated[str | None, Query(max_length=128)] = None,
    delivery_status: DeliveryStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    deliveries = await AlertService(session).list_deliveries(
        _organization_id(actor),
        actor.user_id,
        rule_id=rule_id,
        delivery_status=delivery_status,
        limit=limit,
    )
    return success_response(
        request,
        [AlertDeliveryResponse.model_validate(delivery) for delivery in deliveries],
    )


def _organization_id(actor: AuthContext) -> str:
    if actor.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return actor.organization_id
