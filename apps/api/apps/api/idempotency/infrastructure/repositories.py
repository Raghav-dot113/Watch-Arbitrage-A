from __future__ import annotations

from apps.api.idempotency.infrastructure.models import IdempotencyRecord
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        organization_id: str,
        route_key: str,
        idempotency_key: str,
    ) -> IdempotencyRecord | None:
        result = await self._session.execute(
            select(IdempotencyRecord).where(
                IdempotencyRecord.organization_id == organization_id,
                IdempotencyRecord.route_key == route_key,
                IdempotencyRecord.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()

    async def save(self, record: IdempotencyRecord) -> IdempotencyRecord:
        self._session.add(record)
        await self._session.flush()
        return record
