from __future__ import annotations

from apps.api.infrastructure.repository import BaseRepository, TenantRepository
from apps.api.operations.infrastructure.models import AuditEvent, FeatureFlag, OutboxEvent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AuditEventRepository(TenantRepository[AuditEvent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AuditEvent)

    async def get_by_id(self, id: str, organization_id: str) -> AuditEvent | None:  # type: ignore[override]
        result = await self.session.execute(
            select(AuditEvent).where(
                AuditEvent.id == id,
                AuditEvent.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_org(self, organization_id: str, *, limit: int = 50) -> list[AuditEvent]:  # type: ignore[override]
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        result = await self.session.execute(
            select(AuditEvent)
            .where(AuditEvent.organization_id == organization_id)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class OutboxEventRepository(BaseRepository[OutboxEvent]):
    async def get_by_idempotency_key(self, key: str) -> OutboxEvent | None:
        result = await self.session.execute(
            select(OutboxEvent).where(
                OutboxEvent.event_name == "notification.test_requested",
                OutboxEvent.payload["idempotency_key"].as_string() == key,
            )
        )
        return result.scalar_one_or_none()


class FeatureFlagRepository(BaseRepository[FeatureFlag]):
    async def get_by_key(self, key: str) -> FeatureFlag | None:
        result = await self.session.execute(select(FeatureFlag).where(FeatureFlag.key == key))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[FeatureFlag]:  # type: ignore[override]
        result = await self.session.execute(select(FeatureFlag).order_by(FeatureFlag.key))
        return list(result.scalars().all())
