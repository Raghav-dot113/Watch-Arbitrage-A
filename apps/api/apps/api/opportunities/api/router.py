from __future__ import annotations

from apps.api.identity.api.context import OrganizationContext, get_organization_context
from apps.api.infrastructure.database import get_db
from apps.api.opportunities.api.schemas import OpportunityListResponse, OpportunityResponse
from apps.api.valuation.infrastructure.repositories import OpportunityRepository
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])
_organization_context_dependency = Depends(get_organization_context)
_database_dependency = Depends(get_db)


@router.get(
    "",
    summary="List tenant opportunities",
    description="Returns the authenticated organization's published opportunity feed.",
    response_model=OpportunityListResponse,
    responses={
        401: {"description": "Authentication or tenant membership is required."},
        403: {"description": "The organization role cannot access this resource."},
        422: {"description": "The request is invalid."},
    },
)
async def list_opportunities(
    request: Request,
    limit: int = 50,
    cursor: str | None = None,
    context: OrganizationContext = _organization_context_dependency,
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    if limit < 1 or limit > 100:
        limit = 50
    opportunities, next_cursor = await OpportunityRepository(session).list_for_org(
        organization_id=context.organization_id,
        state="published",
        limit=limit,
        cursor=cursor,
    )
    data = [OpportunityResponse.model_validate(item) for item in opportunities]
    trace_id = getattr(request.state, "trace_id", "unknown")
    response = OpportunityListResponse(
        data=data,
        meta={"trace_id": trace_id, "limit": limit, "next_cursor": next_cursor},
    )
    return JSONResponse(content=response.model_dump(mode="json"))
