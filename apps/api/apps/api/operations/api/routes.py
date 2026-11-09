from __future__ import annotations

from typing import Annotated

from apps.api.identity.api.auth import AuthContext, Permission, require_permissions
from apps.api.infrastructure.api_response import SuccessEnvelope, success_response
from apps.api.infrastructure.database import get_db
from apps.api.operations.api.schemas import (
    AuditEventResponse,
    DuplicateGroupResponse,
    FeatureFlagPatchRequest,
    FeatureFlagResponse,
    SourceAdminResponse,
    SourcePatchRequest,
    UnmatchedListingResponse,
    UnmatchedResolveRequest,
)
from apps.api.operations.application.admin_service import (
    AdminResourceNotFoundError,
    AdminService,
)
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get(
    "/sources",
    response_model=SuccessEnvelope[list[SourceAdminResponse]],
)
async def list_sources(
    request: Request,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    sources = await AdminService(session).list_sources(limit=limit)
    return success_response(
        request,
        [SourceAdminResponse.model_validate(source) for source in sources],
    )


@router.patch(
    "/sources/{source_id}",
    response_model=SuccessEnvelope[SourceAdminResponse],
)
async def update_source(
    source_id: str,
    payload: SourcePatchRequest,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        source = await AdminService(session).set_source_enabled(
            source_id,
            payload.is_enabled,
            actor.user_id,
            trace_id=request.state.trace_id,
        )
    except AdminResourceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    return success_response(request, SourceAdminResponse.model_validate(source))


@router.get(
    "/flags",
    response_model=SuccessEnvelope[list[FeatureFlagResponse]],
)
async def list_feature_flags(
    request: Request,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    flags = await AdminService(session).list_feature_flags(limit=limit)
    return success_response(
        request,
        [FeatureFlagResponse.model_validate(flag) for flag in flags],
    )


@router.patch(
    "/flags/{flag_id}",
    response_model=SuccessEnvelope[FeatureFlagResponse],
)
async def update_feature_flag(
    flag_id: str,
    payload: FeatureFlagPatchRequest,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    patch = payload.model_dump(mode="python", exclude_unset=True)
    try:
        flag = await AdminService(session).update_feature_flag(
            flag_id,
            patch,
            actor.user_id,
            trace_id=request.state.trace_id,
        )
    except AdminResourceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    return success_response(request, FeatureFlagResponse.model_validate(flag))


@router.get(
    "/audit",
    response_model=SuccessEnvelope[list[AuditEventResponse]],
)
async def list_audit_events(
    request: Request,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    events = await AdminService(session).list_audit_events(limit=limit)
    return success_response(
        request,
        [AuditEventResponse.model_validate(event) for event in events],
    )


@router.get(
    "/unmatched",
    response_model=SuccessEnvelope[list[UnmatchedListingResponse]],
)
async def list_unmatched_listings(
    request: Request,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    listings = await AdminService(session).list_unmatched_listings(limit=limit)
    return success_response(
        request,
        [UnmatchedListingResponse.model_validate(listing) for listing in listings],
    )


@router.post(
    "/unmatched/{listing_id}/resolve",
    response_model=SuccessEnvelope[UnmatchedListingResponse],
)
async def resolve_unmatched_listing(
    listing_id: str,
    payload: UnmatchedResolveRequest,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    try:
        listing = await AdminService(session).resolve_unmatched_listing(
            listing_id,
            payload.reference_id,
            actor.user_id,
            trace_id=request.state.trace_id,
        )
    except AdminResourceNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="reference_id must identify an active catalog reference",
        ) from error
    return success_response(
        request,
        UnmatchedListingResponse.model_validate(listing),
    )


@router.get(
    "/duplicates",
    response_model=SuccessEnvelope[list[DuplicateGroupResponse]],
)
async def list_duplicate_groups(
    request: Request,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, object]:
    groups = await AdminService(session).list_duplicate_groups(limit=limit)
    return success_response(
        request,
        [DuplicateGroupResponse.model_validate(group) for group in groups],
    )


@router.get("/jobs", response_model=None)
async def list_jobs(
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
) -> Response:
    return _queue_unavailable()


@router.post("/jobs/{job_id}/replay", response_model=None)
async def replay_job(
    job_id: str,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
) -> Response:
    return _queue_unavailable()


@router.get("/dlq", response_model=None)
async def list_dead_letters(
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
) -> Response:
    return _queue_unavailable()


@router.post("/dlq/{message_id}/replay", response_model=None)
async def replay_dead_letter(
    message_id: str,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
) -> Response:
    return _queue_unavailable()


@router.delete("/dlq/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def discard_dead_letter(
    message_id: str,
    _actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
) -> Response:
    return _queue_unavailable()


def _queue_unavailable() -> Response:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Queue operations are unavailable because no queue backend is configured",
    )
