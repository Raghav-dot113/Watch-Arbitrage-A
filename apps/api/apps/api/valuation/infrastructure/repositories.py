from __future__ import annotations

import base64
import json
from datetime import datetime

from apps.api.infrastructure.repository import BaseRepository, TenantRepository
from apps.api.valuation.infrastructure.models import Opportunity, OpportunityView, Valuation
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


def _encode_cursor(published_at: datetime, opportunity_id: str) -> str:
    payload = json.dumps(
        {"published_at": published_at.isoformat(), "id": opportunity_id},
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    padding = "=" * (-len(cursor) % 4)
    payload = json.loads(base64.urlsafe_b64decode(cursor + padding).decode("utf-8"))
    published_at = datetime.fromisoformat(payload["published_at"])
    opportunity_id = payload["id"]
    if not isinstance(opportunity_id, str):
        raise ValueError("Invalid opportunity cursor")
    return published_at, opportunity_id


class ValuationRepository(BaseRepository[Valuation]):
    async def get_for_listing(self, listing_id: str) -> list[Valuation]:
        result = await self.session.execute(
            select(Valuation)
            .where(Valuation.listing_id == listing_id)
            .order_by(Valuation.created_at.desc(), Valuation.id.desc())
        )
        return list(result.scalars().all())


class OpportunityRepository(TenantRepository[Opportunity]):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, Opportunity)

    async def get_by_id(self, opportunity_id: str, organization_id: str) -> Opportunity | None:
        result = await self.session.execute(
            select(Opportunity).where(
                Opportunity.id == opportunity_id,
                Opportunity.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(
        self,
        organization_id: str,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Opportunity], str | None]:
        if limit < 1:
            raise ValueError("limit must be positive")

        query = (
            select(Opportunity)
            .where(Opportunity.organization_id == organization_id)
            .order_by(Opportunity.published_at.desc(), Opportunity.id.desc())
        )

        if cursor is not None:
            cursor_published_at, cursor_id = _decode_cursor(cursor)
            query = query.where(
                or_(
                    Opportunity.published_at < cursor_published_at,
                    and_(
                        Opportunity.published_at == cursor_published_at,
                        Opportunity.id < cursor_id,
                    ),
                )
            )

        rows = list((await self.session.execute(query.limit(limit + 1))).scalars().all())
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = None
        if has_more and items and items[-1].published_at is not None:
            next_cursor = _encode_cursor(items[-1].published_at, items[-1].id)
        return items, next_cursor

    async def list_for_org(
        self,
        organization_id: str,
        state: str | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Opportunity], str | None]:
        items, next_cursor = await self.list_by_org(
            organization_id=organization_id,
            limit=limit,
            cursor=cursor,
        )
        if state is None:
            return items, next_cursor
        filtered = [item for item in items if item.state == state]
        return filtered, next_cursor

    async def record_view(
        self,
        opportunity_id: str,
        user_id: str,
        organization_id: str,
    ) -> OpportunityView | None:
        opportunity = await self.get_by_id(opportunity_id, organization_id)
        if opportunity is None:
            return None

        result = await self.session.execute(
            select(OpportunityView).where(
                OpportunityView.opportunity_id == opportunity_id,
                OpportunityView.user_id == user_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing

        view = OpportunityView(
            id=generate_ulid("opv"),
            opportunity_id=opportunity_id,
            user_id=user_id,
        )
        self.session.add(view)
        await self.session.flush()
        return view
