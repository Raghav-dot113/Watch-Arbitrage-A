from __future__ import annotations

from apps.api.alerts.infrastructure.models import AlertDelivery, AlertRule
from apps.api.infrastructure.repository import TenantRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AlertRuleRepository(TenantRepository[AlertRule]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AlertRule)

    async def get_by_id(self, id: str, organization_id: str) -> AlertRule | None:  # type: ignore[override]
        result = await self.session.execute(
            select(AlertRule).where(
                AlertRule.id == id,
                AlertRule.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, id: str, organization_id: str) -> AlertRule | None:
        result = await self.session.execute(
            select(AlertRule)
            .where(
                AlertRule.id == id,
                AlertRule.organization_id == organization_id,
            )
            .with_for_update(of=AlertRule)
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, organization_id: str, *, limit: int = 100) -> list[AlertRule]:  # type: ignore[override]
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        result = await self.session.execute(
            select(AlertRule)
            .where(AlertRule.organization_id == organization_id)
            .order_by(AlertRule.created_at.desc(), AlertRule.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class AlertDeliveryRepository(TenantRepository[AlertDelivery]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AlertDelivery)

    async def get_by_id(self, id: str, organization_id: str) -> AlertDelivery | None:  # type: ignore[override]
        result = await self.session.execute(
            select(AlertDelivery).where(
                AlertDelivery.id == id,
                AlertDelivery.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        organization_id: str,
        user_id: str,
        *,
        rule_id: str | None = None,
        delivery_status: str | None = None,
        limit: int = 50,
    ) -> list[AlertDelivery]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        query = select(AlertDelivery).where(
            AlertDelivery.organization_id == organization_id,
            AlertDelivery.user_id == user_id,
        )
        if rule_id is not None:
            query = query.where(AlertDelivery.rule_id == rule_id)
        if delivery_status is not None:
            query = query.where(AlertDelivery.delivery_status == delivery_status)
        result = await self.session.execute(
            query.order_by(AlertDelivery.created_at.desc(), AlertDelivery.id.desc()).limit(limit)
        )
        return list(result.scalars().all())
