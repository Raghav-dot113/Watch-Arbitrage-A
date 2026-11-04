from __future__ import annotations

from apps.api.alerts.infrastructure.models import AlertDelivery, AlertRule
from apps.api.infrastructure.repository import TenantRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AlertRuleRepository(TenantRepository[AlertRule]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AlertRule)

    async def get_by_id(self, id: str, organization_id: str) -> AlertRule | None:
        result = await self.session.execute(
            select(AlertRule).where(
                AlertRule.id == id,
                AlertRule.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, organization_id: str) -> list[AlertRule]:
        result = await self.session.execute(
            select(AlertRule)
            .where(AlertRule.organization_id == organization_id)
            .order_by(AlertRule.created_at.desc(), AlertRule.id.desc())
        )
        return list(result.scalars().all())


class AlertDeliveryRepository(TenantRepository[AlertDelivery]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AlertDelivery)

    async def get_by_id(self, id: str, organization_id: str) -> AlertDelivery | None:
        result = await self.session.execute(
            select(AlertDelivery).where(
                AlertDelivery.id == id,
                AlertDelivery.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, organization_id: str) -> list[AlertDelivery]:
        result = await self.session.execute(
            select(AlertDelivery)
            .where(AlertDelivery.organization_id == organization_id)
            .order_by(AlertDelivery.created_at.desc(), AlertDelivery.id.desc())
        )
        return list(result.scalars().all())
