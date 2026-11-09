from __future__ import annotations

from apps.api.opportunities.api.schemas import OpportunityResponse
from apps.api.pagination import Page
from apps.api.valuation.infrastructure.repositories import OpportunityRepository
from sqlalchemy.ext.asyncio import AsyncSession


class OpportunityService:
    def __init__(self, session: AsyncSession) -> None:
        self._opportunities = OpportunityRepository(session)

    async def list_published(
        self,
        organization_id: str,
        *,
        limit: int,
        cursor: str | None,
    ) -> Page[OpportunityResponse]:
        items, next_cursor = await self._opportunities.list_for_org(
            organization_id=organization_id,
            state="published",
            limit=limit,
            cursor=cursor,
        )
        return Page(
            items=[OpportunityResponse.model_validate(item) for item in items],
            next_cursor=next_cursor,
            has_more=next_cursor is not None,
        )
