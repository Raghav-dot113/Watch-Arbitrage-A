from __future__ import annotations

from apps.api.alerts.infrastructure.models import AlertDelivery
from apps.api.operations.infrastructure.models import OutboxEvent
from sqlalchemy import Text, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

TEST_NOTIFICATION_EVENT = "notification.test_requested"


class NotificationDispatchRepository:
    """Queue reads for the dedicated notification dispatcher process.

    These queries are deliberately cross-tenant: the dispatcher is a system
    worker that drains pending work for every organization. Any request-scoped
    read must stay in the tenant-scoped repositories instead.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _uses_skip_locked(self) -> bool:
        return self.session.get_bind().dialect.name == "postgresql"

    async def list_pending_deliveries(
        self,
        channel: str,
        *,
        limit: int = 50,
    ) -> list[AlertDelivery]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        statement = (
            select(AlertDelivery)
            .where(
                AlertDelivery.channel == channel,
                AlertDelivery.delivery_status == "pending",
            )
            .order_by(AlertDelivery.created_at.asc(), AlertDelivery.id.asc())
            .limit(limit)
        )
        if self._uses_skip_locked():
            statement = statement.with_for_update(skip_locked=True)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_pending_test_notification_events(
        self,
        *,
        limit: int = 50,
    ) -> list[OutboxEvent]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        statement = (
            select(OutboxEvent)
            .where(
                OutboxEvent.event_name == TEST_NOTIFICATION_EVENT,
                OutboxEvent.status == "pending",
                # Keep push/in-app-only events for the workers that own those
                # channels so they cannot starve Telegram work in this queue.
                cast(OutboxEvent.payload, Text).like('%"telegram"%'),
            )
            .order_by(OutboxEvent.created_at.asc(), OutboxEvent.id.asc())
            .limit(limit)
        )
        if self._uses_skip_locked():
            statement = statement.with_for_update(skip_locked=True)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
