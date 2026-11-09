from __future__ import annotations

from apps.api.alerts.api.schemas import AlertRuleRequest, AlertRuleResponse
from apps.api.alerts.application.service import AlertService
from apps.api.idempotency.application.service import IdempotencyKeyReuseError
from apps.api.identity.api.context import OrganizationContext, get_organization_context
from apps.api.identity.api.permissions import require_permission
from apps.api.infrastructure.database import get_db
from apps.api.pagination import (
    InvalidCursorError,
    PaginationParams,
    pagination_params,
)
from apps.api.responses import success_response
from apps.api.schemas import ApiErrorResponse, ApiSuccessEnvelope
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/alerts/rules", tags=["alerts"])
_organization_context_dependency = Depends(get_organization_context)
_create_permission_dependency = Depends(require_permission("alerts:create"))
_database_dependency = Depends(get_db)
_pagination_dependency = Depends(pagination_params)


@router.get(
    "",
    summary="List alert rules",
    description="Lists alert rules belonging to the authenticated organization.",
    response_model=ApiSuccessEnvelope[list[AlertRuleResponse]],
    responses={
        401: {"model": ApiErrorResponse, "description": "Authentication is required."},
        422: {"model": ApiErrorResponse, "description": "The cursor or request is invalid."},
    },
)
async def list_alert_rules(
    request: Request,
    pagination: PaginationParams = _pagination_dependency,
    context: OrganizationContext = _organization_context_dependency,
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    try:
        page = await AlertService(session).list_for_org(
            context.organization_id,
            limit=pagination.limit,
            cursor=pagination.cursor,
        )
    except InvalidCursorError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "The cursor is invalid.",
                "field_errors": {"cursor": [str(exc)]},
            },
        ) from exc
    return success_response(
        page.items,
        getattr(request.state, "trace_id", "unknown"),
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


@router.post(
    "",
    summary="Create an alert rule",
    description="Creates an alert rule using an organization-scoped idempotency key.",
    response_model=ApiSuccessEnvelope[AlertRuleResponse],
    status_code=201,
    responses={
        401: {"model": ApiErrorResponse, "description": "Authentication is required."},
        200: {"model": ApiSuccessEnvelope[AlertRuleResponse], "description": "Idempotent replay."},
        403: {"model": ApiErrorResponse, "description": "The role cannot create rules."},
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
async def create_alert_rule(
    request: Request,
    payload: AlertRuleRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    context: OrganizationContext = _create_permission_dependency,
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    try:
        result = await AlertService(session).create(
            organization_id=context.organization_id,
            user_id=context.user_id,
            trace_id=getattr(request.state, "trace_id", "unknown"),
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
    return success_response(
        result.response_body,
        getattr(request.state, "trace_id", "unknown"),
        status_code=result.status_code,
    )
