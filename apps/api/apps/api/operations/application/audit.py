from __future__ import annotations

from typing import Any

from apps.api.operations.infrastructure.models import AuditEvent
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


async def record_audit_event(
    session: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: str,
    organization_id: str | None = None,
    user_id: str | None = None,
    details: dict[str, Any] | None = None,
    trace_id: str | None = None,
    client_ip: str | None = None,
) -> AuditEvent:
    """Add and flush an audit event within the caller's transaction."""
    for label, value in (
        ("action", action),
        ("resource_type", resource_type),
        ("resource_id", resource_id),
    ):
        if not value.strip():
            raise ValueError(f"{label} must not be empty")

    event = AuditEvent(
        id=generate_ulid("aud"),
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=dict(details) if details is not None else None,
        trace_id=trace_id,
        client_ip=client_ip,
    )
    session.add(event)
    await session.flush()
    return event
