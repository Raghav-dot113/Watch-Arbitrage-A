from __future__ import annotations

import logging
from typing import Annotated

from apps.api.catalog.api.schemas import (
    BrandResponse,
    Channel3SearchRequest,
    ReferenceDetailResponse,
    ReferencePageResponse,
    ReferenceResponse,
    WatchListCreateRequest,
    WatchListResponse,
    WatchListUpdateRequest,
)
from apps.api.catalog.application.channel3 import (
    Channel3NotConfiguredError,
    Channel3SearchGateway,
    Channel3SearchResponse,
    Channel3UnavailableError,
)
from apps.api.catalog.application.service import (
    CatalogService,
    InvalidWatchListReferencesError,
    WatchListNotFoundError,
)
from apps.api.catalog.infrastructure.channel3_client import Channel3Client
from apps.api.identity.api.auth import (
    AuthContext,
    Permission,
    Role,
    require_permissions,
    require_roles,
)
from apps.api.infrastructure.api_response import SuccessEnvelope, success_response
from apps.api.infrastructure.database import get_db
from apps.api.infrastructure.http_status import HTTP_422_UNPROCESSABLE_ENTITY
from apps.api.schemas import ApiErrorResponse
from apps.api.settings import settings
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.errors import ValidationError

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])
logger = logging.getLogger("chronoarb.api")


def get_channel3_search_gateway() -> Channel3SearchGateway:
    return Channel3Client(
        settings.channel3_api_key,
        settings.provider_request_timeout_seconds,
    )


@router.post(
    "/channel3/search",
    summary="Search Channel3 watches",
    description="Search the Channel3 catalog for watch offers.",
    response_model=SuccessEnvelope[Channel3SearchResponse],
    response_model_exclude_none=True,
    responses={
        429: {"model": ApiErrorResponse, "description": "Search provider rate limit reached."},
        502: {
            "model": ApiErrorResponse,
            "description": "Search provider returned an invalid response.",
        },
        503: {
            "model": ApiErrorResponse,
            "description": "Search provider is not configured or unavailable.",
        },
    },
)
async def search_channel3_watches(
    payload: Channel3SearchRequest,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    gateway: Annotated[Channel3SearchGateway, Depends(get_channel3_search_gateway)],
) -> dict[str, object]:
    _organization_id(actor)
    try:
        result = await gateway.search(
            query=payload.query,
            limit=payload.limit,
            page_token=payload.page_token,
        )
    except Channel3NotConfiguredError as error:
        _log_channel3_failure(request, code="not_configured", provider_status_code=None)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "not_configured",
                "message": "Search provider is not configured.",
                "retryable": False,
            },
        ) from error
    except Channel3UnavailableError as error:
        _log_channel3_failure(
            request,
            code=error.code,
            provider_status_code=error.status_code,
        )
        raise HTTPException(
            status_code=(
                status.HTTP_429_TOO_MANY_REQUESTS
                if error.code == "rate_limited"
                else status.HTTP_502_BAD_GATEWAY
                if error.code
                in {"invalid_key", "invalid_provider_response", "provider_rejected_request"}
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "code": error.code,
                "message": error.message,
                "retryable": error.retryable,
            },
        ) from error
    return success_response(request, result)


@router.get(
    "/brands",
    response_model=SuccessEnvelope[list[BrandResponse]],
    response_model_exclude_none=True,
)
async def list_brands(
    request: Request,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    brands = await CatalogService(session).list_brands()
    return success_response(request, [BrandResponse.model_validate(brand) for brand in brands])


@router.get(
    "/references",
    response_model=SuccessEnvelope[list[ReferenceResponse]],
    response_model_exclude_none=True,
)
async def list_references(
    request: Request,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
    q: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    brand_id: Annotated[str | None, Query(max_length=128)] = None,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> dict[str, object]:
    try:
        page = await CatalogService(session).search_references(
            q=q,
            brand_id=brand_id,
            cursor=cursor,
            limit=limit,
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid reference pagination cursor",
        ) from error
    response = ReferencePageResponse(
        items=[ReferenceResponse.model_validate(item) for item in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )
    return success_response(
        request,
        response.items,
        next_cursor=response.next_cursor,
        has_more=response.has_more,
    )


@router.get(
    "/references/{reference_id}",
    response_model=SuccessEnvelope[ReferenceDetailResponse],
    response_model_exclude_none=True,
)
async def get_reference(
    reference_id: str,
    request: Request,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    reference = await CatalogService(session).get_reference(reference_id)
    if reference is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    details = ReferenceDetailResponse(
        **ReferenceResponse.model_validate(reference).model_dump(),
        attributes=reference.attributes,
        aliases=[alias.alias_text for alias in reference.aliases],
    )
    return success_response(request, details)


@router.get(
    "/watch-lists",
    response_model=SuccessEnvelope[list[WatchListResponse]],
    response_model_exclude_none=True,
)
async def list_watch_lists(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    organization_id = _organization_id(actor)
    watch_lists = await CatalogService(session).list_watch_lists(organization_id)
    return success_response(
        request, [WatchListResponse.model_validate(item) for item in watch_lists]
    )


@router.post(
    "/watch-lists",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessEnvelope[WatchListResponse],
    response_model_exclude_none=True,
)
async def create_watch_list(
    payload: WatchListCreateRequest,
    request: Request,
    actor: Annotated[
        AuthContext,
        Depends(require_roles(Role.OWNER, Role.ADMIN, Role.DEALER)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        watch_list = await CatalogService(session).create_watch_list(
            _organization_id(actor),
            name=payload.name,
            reference_ids=payload.reference_ids,
        )
    except InvalidWatchListReferencesError as error:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reference IDs must be unique and identify active catalog references",
        ) from error
    return success_response(request, WatchListResponse.model_validate(watch_list))


@router.put(
    "/watch-lists/{watch_list_id}",
    response_model=SuccessEnvelope[WatchListResponse],
    response_model_exclude_none=True,
)
async def update_watch_list(
    watch_list_id: str,
    payload: WatchListUpdateRequest,
    request: Request,
    actor: Annotated[
        AuthContext,
        Depends(require_roles(Role.OWNER, Role.ADMIN, Role.DEALER)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        watch_list = await CatalogService(session).update_watch_list(
            _organization_id(actor),
            watch_list_id,
            name=payload.name,
            reference_ids=payload.reference_ids,
        )
    except WatchListNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    except InvalidWatchListReferencesError as error:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Reference IDs must be unique and identify active catalog references",
        ) from error
    return success_response(request, WatchListResponse.model_validate(watch_list))


@router.delete("/watch-lists/{watch_list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watch_list(
    watch_list_id: str,
    actor: Annotated[
        AuthContext,
        Depends(require_roles(Role.OWNER, Role.ADMIN, Role.DEALER)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    try:
        await CatalogService(session).delete_watch_list(_organization_id(actor), watch_list_id)
    except WatchListNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error


def _organization_id(actor: AuthContext) -> str:
    if actor.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return actor.organization_id


def _log_channel3_failure(
    request: Request,
    *,
    code: str,
    provider_status_code: int | None,
) -> None:
    logger.warning(
        "channel3_search_failed",
        extra={
            "trace_id": getattr(request.state, "trace_id", "unknown"),
            "provider_status_code": provider_status_code,
            "error_code": code,
        },
    )
