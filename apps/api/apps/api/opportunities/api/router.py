from __future__ import annotations

from apps.api.identity.api.context import OrganizationContext
from apps.api.identity.api.permissions import require_permission
from apps.api.infrastructure.database import get_db
from apps.api.opportunities.api.schemas import OpportunityResponse
from apps.api.opportunities.application.service import OpportunityService
from apps.api.pagination import InvalidCursorError, PaginationParams, pagination_params
from apps.api.responses import success_response
from apps.api.schemas import ApiErrorResponse, ApiSuccessEnvelope
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])
_read_permission_dependency = Depends(require_permission("opportunities:read"))
_database_dependency = Depends(get_db)
_pagination_dependency = Depends(pagination_params)


@router.get(
    "",
    summary="List tenant opportunities",
    description="Returns the authenticated organization's published opportunity feed.",
    response_model=ApiSuccessEnvelope[list[OpportunityResponse]],
    responses={
        401: {"model": ApiErrorResponse, "description": "Authentication is required."},
        403: {"model": ApiErrorResponse, "description": "The role cannot read opportunities."},
        422: {"model": ApiErrorResponse, "description": "The cursor or request is invalid."},
    },
)
async def list_opportunities(
    request: Request,
    pagination: PaginationParams = _pagination_dependency,
    context: OrganizationContext = _read_permission_dependency,
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    try:
        page = await OpportunityService(session).list_published(
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
