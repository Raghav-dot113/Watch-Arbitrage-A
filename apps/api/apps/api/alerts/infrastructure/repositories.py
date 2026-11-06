from __future__ import annotations

from apps.api.alerts.infrastructure.models import AlertRule
from apps.api.infrastructure.repository import TenantRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AlertRuleRepository(TenantRepository[AlertRule]):
    def __init__(self, session: AsyncSession | None = None) -> None:
        super().__init__(session, AlertRule)

    async def list_for_org(self, organization_id: str) -> list[AlertRule]:
        result = await self.session.execute(
            select(AlertRule)
            .where(AlertRule.organization_id == organization_id)
            .order_by(AlertRule.created_at.desc(), AlertRule.id.desc())
        )
        return list(result.scalars().all())
