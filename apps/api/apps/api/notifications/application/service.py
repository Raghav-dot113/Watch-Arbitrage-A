from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from apps.api.alerts.infrastructure.models import AlertDelivery
from apps.api.alerts.infrastructure.repositories import AlertRuleRepository
from apps.api.integrations.application.service import IntegrationService
from apps.api.integrations.application.telegram import TelegramSendResult, TelegramService
from apps.api.notifications.infrastructure.repositories import NotificationDispatchRepository
from apps.api.operations.infrastructure.models import OutboxEvent
from apps.api.opportunities.infrastructure.repositories import OpportunityRepository
from apps.api.settings import Settings
from apps.api.settings import settings as default_settings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("chronoarb.notifications")


class TelegramSender(Protocol):
    """Provider port so notification delivery is testable without network calls."""

    async def send_test_alert(
        self,
        chat_id: str,
        *,
        organization_id: str | None = None,
        rule_id: str | None = None,
        trace_id: str | None = None,
    ) -> TelegramSendResult: ...

    async def send_opportunity_alert(
        self,
        chat_id: str,
        opportunity: dict[str, Any],
        *,
        rule_name: str | None = None,
        base_url: str = "http://localhost:3000",
        trace_id: str | None = None,
    ) -> TelegramSendResult: ...


@dataclass
class DispatchSummary:
    """Counts the work completed by one dispatcher pass."""

    deliveries_sent: int = 0
    deliveries_failed: int = 0
    deliveries_suppressed: int = 0
    test_notifications_sent: int = 0
    test_notifications_failed: int = 0

    @property
    def total(self) -> int:
        return (
            self.deliveries_sent
            + self.deliveries_failed
            + self.deliveries_suppressed
            + self.test_notifications_sent
            + self.test_notifications_failed
        )


class NotificationService:
    """Delivers pending Telegram alert work.

    Alert matching writes ``AlertDelivery`` rows; the alert-rule test route writes
    ``notification.test_requested`` outbox events. This service is the single
    place that turns either into a provider send, so retries and idempotency stay
    in one implementation.
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        telegram: TelegramSender | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.settings = app_settings or default_settings
        self.telegram = telegram or TelegramService()
        self.dispatch = NotificationDispatchRepository(session)
        self.rules = AlertRuleRepository(session)
        self.opportunities = OpportunityRepository(session)
        self.integrations = IntegrationService(session)

    async def dispatch_once(self, *, limit: int = 50) -> DispatchSummary:
        """Sends one bounded batch of pending Telegram notifications."""
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        summary = DispatchSummary()

        deliveries = await self.dispatch.list_pending_deliveries("telegram", limit=limit)
        for delivery in deliveries:
            await self._deliver_alert(delivery, summary)

        events = await self.dispatch.list_pending_test_notification_events(limit=limit)
        for event in events:
            await self._deliver_test_event(event, summary)

        return summary

    async def _deliver_alert(
        self,
        delivery: AlertDelivery,
        summary: DispatchSummary,
    ) -> None:
        rule = await self.rules.get_by_id(delivery.rule_id, delivery.organization_id)
        if rule is None:
            logger.warning(
                "suppressing alert delivery for missing rule",
                extra={"delivery_id": delivery.id, "rule_id": delivery.rule_id},
            )
            await self._finish_delivery(delivery, "failed")
            summary.deliveries_failed += 1
            return

        opportunity = await self.opportunities.get_detail(
            delivery.opportunity_id,
            delivery.organization_id,
        )
        if opportunity is None:
            logger.warning(
                "suppressing alert delivery for missing opportunity",
                extra={
                    "delivery_id": delivery.id,
                    "opportunity_id": delivery.opportunity_id,
                },
            )
            await self._finish_delivery(delivery, "failed")
            summary.deliveries_failed += 1
            return

        chat_id = await self.integrations.get_effective_telegram_chat_id(
            delivery.organization_id,
            delivery.user_id,
        )
        if not chat_id:
            logger.info(
                "suppressing alert delivery with no Telegram destination",
                extra={"delivery_id": delivery.id, "user_id": delivery.user_id},
            )
            await self._finish_delivery(delivery, "suppressed")
            summary.deliveries_suppressed += 1
            return

        try:
            result = await self.telegram.send_opportunity_alert(
                chat_id,
                dict(opportunity),
                rule_name=rule.name,
                base_url=self.settings.web_base_url,
            )
        except Exception:
            logger.exception(
                "unexpected error sending Telegram alert",
                extra={"delivery_id": delivery.id},
            )
            await self._finish_delivery(delivery, "failed")
            summary.deliveries_failed += 1
            return

        if result.success:
            await self._finish_delivery(
                delivery,
                "sent",
                provider_message_id=result.provider_message_id,
            )
            summary.deliveries_sent += 1
            logger.info(
                "Telegram alert delivered",
                extra={
                    "delivery_id": delivery.id,
                    "provider_message_id": result.provider_message_id,
                },
            )
            return

        logger.warning(
            "Telegram alert delivery failed",
            extra={
                "delivery_id": delivery.id,
                "status_code": result.status_code,
                "error": result.error_message,
            },
        )
        await self._finish_delivery(delivery, "failed")
        summary.deliveries_failed += 1

    async def _deliver_test_event(
        self,
        event: OutboxEvent,
        summary: DispatchSummary,
    ) -> None:
        payload = event.payload or {}
        channels = payload.get("channels") or []
        if "telegram" not in channels:
            # Another channel worker owns this event; leave it pending instead of
            # acknowledging work this process cannot perform.
            return

        organization_id = payload.get("organization_id")
        user_id = payload.get("user_id")
        rule_id = payload.get("rule_id")
        if not organization_id or not user_id or not rule_id:
            logger.warning(
                "failing malformed test notification event",
                extra={"event_id": event.id},
            )
            await self._finish_event(event, "failed")
            summary.test_notifications_failed += 1
            return

        chat_id = await self.integrations.get_effective_telegram_chat_id(
            str(organization_id),
            str(user_id),
        )
        if not chat_id:
            logger.info(
                "failing test notification with no Telegram destination",
                extra={"event_id": event.id, "user_id": user_id},
            )
            await self._finish_event(event, "failed")
            summary.test_notifications_failed += 1
            return

        try:
            result = await self.telegram.send_test_alert(
                chat_id,
                organization_id=str(organization_id),
                rule_id=str(rule_id),
                trace_id=event.trace_id,
            )
        except Exception:
            logger.exception(
                "unexpected error sending Telegram test notification",
                extra={"event_id": event.id},
            )
            await self._finish_event(event, "failed")
            summary.test_notifications_failed += 1
            return

        if result.success:
            await self._finish_event(event, "published")
            summary.test_notifications_sent += 1
            logger.info(
                "Telegram test notification delivered",
                extra={
                    "event_id": event.id,
                    "provider_message_id": result.provider_message_id,
                },
            )
            return

        logger.warning(
            "Telegram test notification failed",
            extra={
                "event_id": event.id,
                "status_code": result.status_code,
                "error": result.error_message,
            },
        )
        await self._finish_event(event, "failed")
        summary.test_notifications_failed += 1

    async def _finish_delivery(
        self,
        delivery: AlertDelivery,
        status: str,
        *,
        provider_message_id: str | None = None,
    ) -> None:
        delivery.delivery_status = status
        if provider_message_id is not None:
            delivery.provider_message_id = provider_message_id
        await self.session.commit()

    async def _finish_event(self, event: OutboxEvent, status: str) -> None:
        event.status = status
        if status == "published":
            event.published_at = datetime.now(UTC)
        await self.session.commit()
