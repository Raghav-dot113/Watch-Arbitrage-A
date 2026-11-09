from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from apps.api.alerts.api.schemas import AlertRuleCreateRequest
from apps.api.alerts.infrastructure.models import AlertDelivery, AlertRule
from apps.api.alerts.infrastructure.repositories import (
    AlertDeliveryRepository,
    AlertRuleRepository,
)
from apps.api.infrastructure.idempotency import make_idempotency_identity
from apps.api.operations.application.audit import record_audit_event
from apps.api.operations.application.outbox import record_outbox_event
from apps.api.operations.infrastructure.repositories import OutboxEventRepository
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


class AlertRuleNotFoundError(Exception):
    pass


class AlertRuleDisabledError(Exception):
    pass


class AlertTestIdempotencyConflictError(Exception):
    pass


@dataclass(frozen=True)
class AlertTestResult:
    event_id: str
    created: bool


class AlertService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.rules = AlertRuleRepository(session)
        self.deliveries = AlertDeliveryRepository(session)
        self.outbox = OutboxEventRepository(session)

    async def list_rules(self, organization_id: str, *, limit: int) -> list[AlertRule]:
        return await self.rules.list_by_org(organization_id, limit=limit)

    async def get_rule(self, organization_id: str, rule_id: str) -> AlertRule | None:
        return await self.rules.get_by_id(rule_id, organization_id)

    async def create_rule(
        self,
        organization_id: str,
        user_id: str,
        payload: AlertRuleCreateRequest,
        *,
        trace_id: str,
    ) -> AlertRule:
        rule = AlertRule(
            id=generate_ulid("alr"),
            organization_id=organization_id,
            created_by=user_id,
            name=payload.name,
            filters=payload.filters.model_dump(mode="json", exclude_none=True),
            channels=list(payload.channels),
            cooldown_minutes=payload.cooldown_minutes,
            is_enabled=payload.is_enabled,
        )
        self.session.add(rule)
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="alert_rule.created",
            resource_type="alert_rule",
            resource_id=rule.id,
            trace_id=trace_id,
        )
        await self.session.commit()
        return rule

    async def update_rule(
        self,
        organization_id: str,
        user_id: str,
        rule_id: str,
        payload: AlertRuleCreateRequest,
        *,
        trace_id: str,
    ) -> AlertRule:
        rule = await self.rules.get_by_id_for_update(rule_id, organization_id)
        if rule is None:
            raise AlertRuleNotFoundError
        rule.name = payload.name
        rule.filters = payload.filters.model_dump(mode="json", exclude_none=True)
        rule.channels = list(payload.channels)
        rule.cooldown_minutes = payload.cooldown_minutes
        rule.is_enabled = payload.is_enabled
        rule.updated_at = datetime.now(UTC)
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="alert_rule.updated",
            resource_type="alert_rule",
            resource_id=rule.id,
            trace_id=trace_id,
        )
        await self.session.commit()
        return rule

    async def disable_rule(
        self,
        organization_id: str,
        user_id: str,
        rule_id: str,
        *,
        trace_id: str,
    ) -> None:
        rule = await self.rules.get_by_id_for_update(rule_id, organization_id)
        if rule is None:
            raise AlertRuleNotFoundError
        if not rule.is_enabled:
            return
        rule.is_enabled = False
        rule.updated_at = datetime.now(UTC)
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="alert_rule.disabled",
            resource_type="alert_rule",
            resource_id=rule.id,
            trace_id=trace_id,
        )
        await self.session.commit()

    async def list_deliveries(
        self,
        organization_id: str,
        user_id: str,
        *,
        rule_id: str | None,
        delivery_status: str | None,
        limit: int,
    ) -> list[AlertDelivery]:
        return await self.deliveries.list_for_user(
            organization_id,
            user_id,
            rule_id=rule_id,
            delivery_status=delivery_status,
            limit=limit,
        )

    async def request_test_notification(
        self,
        organization_id: str,
        user_id: str,
        rule_id: str,
        idempotency_key: str,
        *,
        trace_id: str,
    ) -> AlertTestResult:
        rule = await self.rules.get_by_id_for_update(rule_id, organization_id)
        if rule is None:
            raise AlertRuleNotFoundError
        if not rule.is_enabled:
            raise AlertRuleDisabledError
        request_payload: dict[str, Any] = {"channels": list(rule.channels)}
        identity = make_idempotency_identity(
            key=idempotency_key,
            organization_id=organization_id,
            user_id=user_id,
            operation=f"alert.test:{rule_id}",
            payload=request_payload,
        )
        existing = await self.outbox.get_by_idempotency_key(identity.storage_key)
        if existing is not None:
            if existing.payload.get("request_fingerprint") != identity.request_fingerprint:
                raise AlertTestIdempotencyConflictError
            return AlertTestResult(existing.id, False)

        event = await record_outbox_event(
            self.session,
            event_name="notification.test_requested",
            event_version="1",
            payload={
                **request_payload,
                "organization_id": organization_id,
                "user_id": user_id,
                "rule_id": rule_id,
                "idempotency_key": identity.storage_key,
                "request_fingerprint": identity.request_fingerprint,
            },
            trace_id=trace_id,
        )
        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="alert_rule.test_requested",
            resource_type="alert_rule",
            resource_id=rule.id,
            details={"outbox_event_id": event.id},
            trace_id=trace_id,
        )
        await self.session.commit()
        return AlertTestResult(event.id, True)
