from __future__ import annotations

from typing import Any

from apps.api.alerts.api.schemas import AlertRuleRequest, AlertRuleResponse
from apps.api.alerts.infrastructure.models import AlertRule
from apps.api.alerts.infrastructure.repositories import AlertRuleRepository
from apps.api.idempotency.application.service import IdempotencyResult, IdempotencyService
from apps.api.operations.application.audit import AuditService
from apps.api.pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


class AlertService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._rules = AlertRuleRepository(session)

    async def list_for_org(
        self,
        organization_id: str,
        *,
        limit: int,
        cursor: str | None,
    ) -> Page[AlertRuleResponse]:
        page = await self._rules.list_for_org(
            organization_id,
            limit=limit,
            cursor=cursor,
        )
        return Page(
            items=[AlertRuleResponse.model_validate(rule) for rule in page.items],
            next_cursor=page.next_cursor,
            has_more=page.has_more,
        )

    async def create(
        self,
        *,
        organization_id: str,
        user_id: str,
        trace_id: str,
        idempotency_key: str,
        request: AlertRuleRequest,
    ) -> IdempotencyResult:
        async def create_rule() -> tuple[int, dict[str, Any]]:
            rule = AlertRule(
                id=generate_ulid("alr"),
                organization_id=organization_id,
                created_by=user_id,
                name=request.name,
                filters=request.filters,
                channels=request.channels,
                cooldown_minutes=request.cooldown_minutes,
                is_enabled=request.is_enabled,
            )
            await self._rules.save(rule)
            await AuditService(self._session).record(
                action="alert_rule.created",
                resource_type="alert_rule",
                resource_id=rule.id,
                organization_id=organization_id,
                user_id=user_id,
                trace_id=trace_id,
            )
            response = AlertRuleResponse.model_validate(rule)
            return 201, response.model_dump(mode="json")

        return await IdempotencyService(self._session).execute(
            organization_id=organization_id,
            route_key="POST:/api/v1/alerts/rules",
            key=idempotency_key,
            request_body=request.model_dump(mode="json"),
            operation=create_rule,
        )
