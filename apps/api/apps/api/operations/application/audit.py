from __future__ import annotations

from typing import Any

from apps.api.operations.infrastructure.models import AuditEvent
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str,
        organization_id: str | None,
        user_id: str | None,
        trace_id: str | None,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=generate_ulid("aud"),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=organization_id,
            user_id=user_id,
            trace_id=trace_id,
            details=details,
        )
        self._session.add(event)
        await self._session.flush()
        return event
