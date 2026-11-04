from __future__ import annotations

from typing import Annotated

from apps.api.identity.api.auth import AuthContext, Permission, require_permissions
from apps.api.infrastructure.api_response import SuccessEnvelope, success_response
from apps.api.infrastructure.database import get_db
from apps.api.integrations.api.schemas import (
    IntegrationStatusResponse,
    PushDeviceCreateRequest,
    PushDeviceResponse,
    TelegramLinkResponse,
)
from apps.api.integrations.application.crypto import IntegrationEncryptionUnavailableError
from apps.api.integrations.application.service import (
    DeviceTokenConflictError,
    IntegrationService,
    ProviderIntegrationNotFoundError,
    TelegramLinkUnavailableError,
)
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/settings/integrations", tags=["integrations"])


@router.get(
    "",
    response_model=SuccessEnvelope[IntegrationStatusResponse],
    response_model_exclude_none=True,
)
async def get_integration_status(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    result = await IntegrationService(session).get_status(
        _organization_id(actor),
        actor.user_id,
    )
    return success_response(request, IntegrationStatusResponse.model_validate(result))


@router.post(
    "/telegram",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[TelegramLinkResponse],
)
async def link_telegram(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.ALERTS_CREATE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        link = await IntegrationService(session).start_telegram_link(
            _organization_id(actor),
            actor.user_id,
            trace_id=request.state.trace_id,
        )
    except TelegramLinkUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram linking is not configured",
        ) from error
    return success_response(
        request,
        TelegramLinkResponse(link_url=link.url, expires_at=link.expires_at),
    )


@router.delete("/telegram", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_telegram(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.ALERTS_CREATE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    await IntegrationService(session).unlink_telegram(
        _organization_id(actor),
        actor.user_id,
        trace_id=request.state.trace_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/push",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[PushDeviceResponse],
)
async def register_push_device(
    payload: PushDeviceCreateRequest,
    request: Request,
    http_response: Response,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        device, created = await IntegrationService(session).register_push_device(
            _organization_id(actor),
            actor.user_id,
            payload,
            trace_id=request.state.trace_id,
        )
    except DeviceTokenConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Push device token is already registered to another account",
        ) from error
    except IntegrationEncryptionUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Secure integration storage is not configured",
        ) from error
    if not created:
        http_response.status_code = status.HTTP_200_OK
    return success_response(request, PushDeviceResponse.model_validate(device))


@router.delete("/push/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_push_device(
    device_id: str,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await IntegrationService(session).unregister_push_device(
            _organization_id(actor),
            actor.user_id,
            device_id,
            trace_id=request.state.trace_id,
        )
    except ProviderIntegrationNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _organization_id(actor: AuthContext) -> str:
    if actor.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return actor.organization_id
