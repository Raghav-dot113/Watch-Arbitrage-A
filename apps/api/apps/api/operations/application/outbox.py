from __future__ import annotations

from typing import Any

from apps.api.operations.infrastructure.models import OutboxEvent
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


async def record_outbox_event(
    session: AsyncSession,
    *,
    event_name: str,
    event_version: str,
    payload: dict[str, Any],
    trace_id: str | None,
) -> OutboxEvent:
    event = OutboxEvent(
        id=generate_ulid("evt"),
        event_name=event_name,
        event_version=event_version,
        payload=dict(payload),
        trace_id=trace_id,
        status="pending",
    )
    session.add(event)
    await session.flush()
    return event
