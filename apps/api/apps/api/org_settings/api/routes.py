from __future__ import annotations

from typing import Annotated

from apps.api.identity.api.auth import AuthContext, Permission, require_permissions
from apps.api.infrastructure.api_response import SuccessEnvelope, success_response
from apps.api.infrastructure.database import get_db
from apps.api.org_settings.api.schemas import (
    OrganizationSettingsPatchRequest,
    OrganizationSettingsResponse,
)
from apps.api.org_settings.application.service import (
    OrganizationSettingsNotFoundError,
    SettingsService,
)
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get(
    "/organization",
    response_model=SuccessEnvelope[OrganizationSettingsResponse],
)
async def get_organization_settings(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        settings_response = await SettingsService(session).get_organization_settings(
            _organization_id(actor)
        )
    except OrganizationSettingsNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    return success_response(request, settings_response)


@router.patch(
    "/organization",
    response_model=SuccessEnvelope[OrganizationSettingsResponse],
)
async def patch_organization_settings(
    payload: OrganizationSettingsPatchRequest,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.MEMBERS_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        settings_response = await SettingsService(session).patch_organization_settings(
            _organization_id(actor),
            actor.user_id,
            payload,
            trace_id=request.state.trace_id,
        )
    except OrganizationSettingsNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    return success_response(request, settings_response)


def _organization_id(actor: AuthContext) -> str:
    if actor.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return actor.organization_id
