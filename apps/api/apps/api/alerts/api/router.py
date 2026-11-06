from __future__ import annotations

from apps.api.alerts.api.schemas import AlertRuleRequest, AlertRuleResponse
from apps.api.alerts.infrastructure.models import AlertRule
from apps.api.alerts.infrastructure.repositories import AlertRuleRepository
from apps.api.identity.api.context import OrganizationContext, get_organization_context
from apps.api.infrastructure.database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid

router = APIRouter(prefix="/api/v1/alerts/rules", tags=["alerts"])
_organization_context_dependency = Depends(get_organization_context)
_database_dependency = Depends(get_db)


@router.get(
    "",
    summary="List alert rules",
    description="Lists alert rules belonging to the authenticated organization.",
    response_model=list[AlertRuleResponse],
)
async def list_alert_rules(
    context: OrganizationContext = _organization_context_dependency,
    session: AsyncSession = _database_dependency,
) -> list[AlertRuleResponse]:
    rules = await AlertRuleRepository(session).list_for_org(context.organization_id)
    return [AlertRuleResponse.model_validate(rule) for rule in rules]


@router.post(
    "",
    summary="Create an alert rule",
    description="Creates a tenant-scoped alert rule.",
    response_model=AlertRuleResponse,
    status_code=201,
    responses={
        401: {"description": "Authentication or organization membership is required."},
        403: {"description": "The organization role cannot create rules."},
        422: {"description": "The alert rule payload is invalid."},
    },
)
async def create_alert_rule(
    payload: AlertRuleRequest,
    context: OrganizationContext = _organization_context_dependency,
    session: AsyncSession = _database_dependency,
) -> AlertRuleResponse:
    if context.role not in {"owner", "admin"}:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Insufficient organization role")
    rule = AlertRule(
        id=generate_ulid("alr"),
        organization_id=context.organization_id,
        created_by=context.user_id,
        name=payload.name,
        filters=payload.filters,
        channels=payload.channels,
        cooldown_minutes=payload.cooldown_minutes,
        is_enabled=payload.is_enabled,
    )
    await AlertRuleRepository(session).save(rule)
    await session.commit()
    return AlertRuleResponse.model_validate(rule)
