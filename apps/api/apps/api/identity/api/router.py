from __future__ import annotations

from apps.api.identity.api.auth import get_current_subject
from apps.api.identity.api.schemas import (
    ErrorResponse,
    OrganizationListResponse,
)
from apps.api.identity.application.services import IdentityService
from apps.api.infrastructure.database import get_db
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])
_current_subject_dependency = Depends(get_current_subject)
_database_dependency = Depends(get_db)


@router.get(
    "/organizations",
    summary="List current user's organizations",
    description="Returns only organizations where the authenticated user has membership.",
    response_model=OrganizationListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication is required."},
        422: {"model": ErrorResponse, "description": "The request is invalid."},
    },
)
async def list_organizations(
    request: Request,
    subject: str = _current_subject_dependency,
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    organizations = await IdentityService(session).list_organizations_for_subject(subject)
    trace_id = getattr(request.state, "trace_id", "unknown")
    response = OrganizationListResponse(
        data=organizations,
        meta={"trace_id": trace_id},
    )
    return JSONResponse(content=response.model_dump(mode="json"))
