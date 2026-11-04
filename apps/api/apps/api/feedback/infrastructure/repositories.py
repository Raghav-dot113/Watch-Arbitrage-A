from __future__ import annotations

from apps.api.feedback.infrastructure.models import Feedback, TradeOutcome
from apps.api.infrastructure.repository import TenantRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class FeedbackRepository(TenantRepository[Feedback]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Feedback)

    async def get_by_id(self, id: str, organization_id: str) -> Feedback | None:  # type: ignore[override]
        result = await self.session.execute(
            select(Feedback).where(
                Feedback.id == id,
                Feedback.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_opportunity(
        self, opportunity_id: str, organization_id: str
    ) -> list[Feedback]:
        result = await self.session.execute(
            select(Feedback)
            .where(
                Feedback.opportunity_id == opportunity_id,
                Feedback.organization_id == organization_id,
            )
            .order_by(Feedback.created_at.desc(), Feedback.id.desc())
        )
        return list(result.scalars().all())

    async def get_by_idempotency_key(
        self, key: str, organization_id: str, user_id: str
    ) -> Feedback | None:
        result = await self.session.execute(
            select(Feedback).where(
                Feedback.idempotency_key == key,
                Feedback.organization_id == organization_id,
                Feedback.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, organization_id: str, *, limit: int = 100) -> list[Feedback]:  # type: ignore[override]
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        result = await self.session.execute(
            select(Feedback)
            .where(Feedback.organization_id == organization_id)
            .order_by(Feedback.created_at.desc(), Feedback.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class TradeOutcomeRepository(TenantRepository[TradeOutcome]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TradeOutcome)

    async def get_by_id(self, id: str, organization_id: str) -> TradeOutcome | None:  # type: ignore[override]
        result = await self.session.execute(
            select(TradeOutcome).where(
                TradeOutcome.id == id,
                TradeOutcome.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_opportunity(
        self, opportunity_id: str, organization_id: str
    ) -> list[TradeOutcome]:
        result = await self.session.execute(
            select(TradeOutcome)
            .where(
                TradeOutcome.opportunity_id == opportunity_id,
                TradeOutcome.organization_id == organization_id,
            )
            .order_by(TradeOutcome.created_at.desc(), TradeOutcome.id.desc())
        )
        return list(result.scalars().all())

    async def list_by_org(self, organization_id: str, *, limit: int = 100) -> list[TradeOutcome]:  # type: ignore[override]
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        result = await self.session.execute(
            select(TradeOutcome)
            .where(TradeOutcome.organization_id == organization_id)
            .order_by(TradeOutcome.created_at.desc(), TradeOutcome.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_idempotency_key(
        self, key: str, organization_id: str, user_id: str
    ) -> TradeOutcome | None:
        result = await self.session.execute(
            select(TradeOutcome).where(
                TradeOutcome.idempotency_key == key,
                TradeOutcome.organization_id == organization_id,
                TradeOutcome.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
