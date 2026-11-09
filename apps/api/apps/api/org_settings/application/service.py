from __future__ import annotations

from typing import Any

from apps.api.identity.infrastructure.models import Organization
from apps.api.operations.application.audit import record_audit_event
from apps.api.org_settings.api.schemas import (
    FeeDefaults,
    OrganizationSettingsPatchRequest,
    OrganizationSettingsResponse,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class OrganizationSettingsNotFoundError(Exception):
    pass


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_organization_settings(self, organization_id: str) -> OrganizationSettingsResponse:
        organization = await self.session.get(Organization, organization_id)
        if organization is None:
            raise OrganizationSettingsNotFoundError
        data: dict[str, Any] = organization.settings or {}
        return OrganizationSettingsResponse(
            currency=data.get("currency", "USD"),
            timezone=data.get("timezone", "UTC"),
            default_fees=FeeDefaults.model_validate(data.get("default_fees", {})),
        )

    async def patch_organization_settings(
        self,
        organization_id: str,
        user_id: str,
        payload: OrganizationSettingsPatchRequest,
        *,
        trace_id: str,
    ) -> OrganizationSettingsResponse:
        result = await self.session.execute(
            select(Organization)
            .where(Organization.id == organization_id)
            .with_for_update(of=Organization)
        )
        organization = result.scalar_one_or_none()
        if organization is None:
            raise OrganizationSettingsNotFoundError

        updated: dict[str, Any] = dict(organization.settings or {})
        if "currency" in payload.model_fields_set:
            updated["currency"] = payload.currency
        if "timezone" in payload.model_fields_set:
            updated["timezone"] = payload.timezone
        if "default_fees" in payload.model_fields_set:
            if payload.default_fees is None:
                updated.pop("default_fees", None)
            else:
                fee_defaults = dict(updated.get("default_fees", {}))
                for field_name in payload.default_fees.model_fields_set:
                    value = getattr(payload.default_fees, field_name)
                    if value is None:
                        fee_defaults.pop(field_name, None)
                    else:
                        fee_defaults[field_name] = str(value)
                updated["default_fees"] = fee_defaults
        organization.settings = updated

        await record_audit_event(
            self.session,
            organization_id=organization_id,
            user_id=user_id,
            action="organization.settings_updated",
            resource_type="organization",
            resource_id=organization_id,
            details={"fields": sorted(payload.model_fields_set)},
            trace_id=trace_id,
        )
        await self.session.commit()
        return await self.get_organization_settings(organization_id)
