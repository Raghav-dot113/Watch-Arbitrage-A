from __future__ import annotations

from apps.api.feedback.infrastructure.models import Feedback, TradeOutcome
from apps.api.infrastructure.repository import TenantRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class FeedbackRepository(TenantRepository[Feedback]):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, Feedback)

    async def get_by_idempotency_key(
        self,
        organization_id: str,
        idempotency_key: str,
    ) -> Feedback | None:
        result = await self.session.execute(
            select(Feedback).where(
                Feedback.organization_id == organization_id,
                Feedback.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()


class TradeOutcomeRepository(TenantRepository[TradeOutcome]):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, TradeOutcome)
