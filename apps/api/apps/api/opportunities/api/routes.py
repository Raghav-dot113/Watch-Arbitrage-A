from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from apps.api.identity.api.auth import AuthContext, Permission, require_permissions
from apps.api.infrastructure.api_response import SuccessEnvelope, success_response
from apps.api.infrastructure.database import get_db
from apps.api.infrastructure.http_status import HTTP_422_UNPROCESSABLE_ENTITY
from apps.api.opportunities.api.schemas import (
    OpportunityDetailResponse,
    OpportunityFeedItem,
)
from apps.api.opportunities.application.service import OpportunityService
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.errors import ValidationError

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])

OpportunitySort = Literal["newest", "score_desc", "profit_desc", "roi_desc"]
OpportunityState = Literal["published", "dismissed", "contacted", "purchased", "expired"]


@router.get(
    "",
    response_model=SuccessEnvelope[list[OpportunityFeedItem]],
)
async def list_opportunities(
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    sort: OpportunitySort = "score_desc",
    state: OpportunityState | None = "published",
    reference_id: Annotated[str | None, Query(max_length=128)] = None,
    brand_id: Annotated[str | None, Query(max_length=128)] = None,
    condition: Annotated[str | None, Query(max_length=64)] = None,
    min_roi: Decimal | None = None,
    min_profit: Decimal | None = None,
    min_confidence: Annotated[Decimal | None, Query(ge=0, le=1)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    watch_list_id: Annotated[str | None, Query(max_length=128)] = None,
) -> dict[str, object]:
    if actor.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    try:
        items, next_cursor, has_more = await OpportunityService(session).list_feed(
            actor.organization_id,
            user_id=actor.user_id,
            limit=limit,
            cursor=cursor,
            sort=sort,
            state=state,
            reference_id=reference_id,
            brand_id=brand_id,
            condition=condition,
            min_roi=min_roi,
            min_profit=min_profit,
            min_confidence=min_confidence,
            q=q,
            watch_list_id=watch_list_id,
        )
    except ValidationError as error:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid opportunity pagination cursor",
        ) from error
    return success_response(
        request,
        items,
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.get(
    "/{opportunity_id}",
    response_model=SuccessEnvelope[OpportunityDetailResponse],
)
async def get_opportunity(
    opportunity_id: str,
    request: Request,
    actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, object]:
    if actor.organization_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    detail = await OpportunityService(session).get_detail(
        opportunity_id,
        actor.organization_id,
        user_id=actor.user_id,
    )
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return success_response(request, detail)
