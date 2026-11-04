from __future__ import annotations

from apps.api.billing.infrastructure.models import Subscription
from apps.api.infrastructure.repository import TenantRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class SubscriptionRepository(TenantRepository[Subscription]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Subscription)

    async def get_by_id(self, id: str, organization_id: str) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.id == id,
                Subscription.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_for_org(self, organization_id: str) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.organization_id == organization_id)
            .order_by(Subscription.created_at.desc(), Subscription.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
