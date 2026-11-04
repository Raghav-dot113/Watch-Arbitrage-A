from __future__ import annotations

from typing import Annotated

from apps.api.identity.api.auth import (
    AuthContext,
    AuthenticatedUser,
    Permission,
    get_authenticated_user,
    require_permissions,
)
from apps.api.identity.api.schemas import (
    CurrentUserResponse,
    MembershipResponse,
    OrganizationCreateRequest,
    OrganizationMemberResponse,
    OrganizationMembershipResponse,
    OrganizationPatchRequest,
    OrganizationResponse,
    UserResponse,
)
from apps.api.identity.application.service import (
    IdentityService,
    OrganizationNotFoundError,
    OrganizationSlugConflictError,
)
from apps.api.infrastructure.api_response import SuccessEnvelope, success_response
from apps.api.infrastructure.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])


@router.get(
    "/me",
    response_model=SuccessEnvelope[CurrentUserResponse],
    response_model_exclude_none=True,
)
async def get_me(
    request: Request,
    identity: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        user, memberships = await IdentityService(session).current_user(identity.user_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from error
    response = CurrentUserResponse(
        user=UserResponse.model_validate(user),
        memberships=[
            OrganizationMembershipResponse(
                **MembershipResponse.model_validate(membership).model_dump(),
                organization=OrganizationResponse.model_validate(membership.organization),
            )
            for membership in memberships
        ],
    )
    return success_response(request, response)


@router.post(
    "/organizations",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[OrganizationResponse],
    response_model_exclude_none=True,
)
async def create_organization(
    payload: OrganizationCreateRequest,
    request: Request,
    identity: Annotated[AuthenticatedUser, Depends(get_authenticated_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        organization = await IdentityService(session).create_organization(
            identity.user_id,
            name=payload.name,
            slug=payload.slug,
        )
    except OrganizationSlugConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization slug is already in use",
        ) from error
    return success_response(request, OrganizationResponse.model_validate(organization))


@router.get(
    "/organizations/{org_id}",
    response_model=SuccessEnvelope[OrganizationResponse],
    response_model_exclude_none=True,
)
async def get_organization(
    org_id: str,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        organization = await IdentityService(session).get_organization(
            actor.organization_id or "", org_id
        )
    except OrganizationNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    return success_response(request, OrganizationResponse.model_validate(organization))


@router.patch(
    "/organizations/{org_id}",
    response_model=SuccessEnvelope[OrganizationResponse],
    response_model_exclude_none=True,
)
async def patch_organization(
    org_id: str,
    payload: OrganizationPatchRequest,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.MEMBERS_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        organization = await IdentityService(session).update_organization(
            actor.organization_id or "",
            org_id,
            name=payload.name,
            settings=payload.settings,
            update_settings="settings" in payload.model_fields_set,
        )
    except OrganizationNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    return success_response(request, OrganizationResponse.model_validate(organization))


@router.get(
    "/organizations/{org_id}/members",
    response_model=SuccessEnvelope[list[OrganizationMemberResponse]],
    response_model_exclude_none=True,
)
async def list_organization_members(
    org_id: str,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        await IdentityService(session).get_organization(actor.organization_id or "", org_id)
    except OrganizationNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    memberships = await IdentityService(session).list_members(org_id)
    members = [
        OrganizationMemberResponse(
            **MembershipResponse.model_validate(membership).model_dump(),
            email=membership.user.email,
            display_name=membership.user.display_name,
        )
        for membership in memberships
    ]
    return success_response(request, members)
