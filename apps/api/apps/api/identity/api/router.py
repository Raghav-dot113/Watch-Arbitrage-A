from __future__ import annotations

from apps.api.identity.api.auth import get_current_subject
from apps.api.identity.api.schemas import (
    CurrentUserResponse,
    ErrorResponse,
    UserOrganizationResponse,
)
from apps.api.identity.application.service import IdentityService
from apps.api.infrastructure.database import get_db
from apps.api.responses import success_response
from apps.api.schemas import ApiSuccessEnvelope
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])
_current_subject_dependency = Depends(get_current_subject)
_database_dependency = Depends(get_db)


@router.get(
    "/me",
    summary="Get current user",
    description="Returns the authenticated user's profile and organization memberships.",
    response_model=ApiSuccessEnvelope[CurrentUserResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication or identity is invalid."},
    },
)
async def get_current_user(
    request: Request,
    subject: str = _current_subject_dependency,
    session: AsyncSession = _database_dependency,
) -> JSONResponse:
    profile = await IdentityService(session).get_current_user_for_subject(subject)
    return success_response(profile, getattr(request.state, "trace_id", "unknown"))


@router.get(
    "/organizations",
    summary="List current user's organizations",
    description="Returns only organizations where the authenticated user has membership.",
    response_model=ApiSuccessEnvelope[list[UserOrganizationResponse]],
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
    return success_response(
        organizations,
        getattr(request.state, "trace_id", "unknown"),
    )
