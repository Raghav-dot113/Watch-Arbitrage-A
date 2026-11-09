from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceAdminResponse(BaseModel):
    id: str
    source_key: str
    display_name: str
    adapter_version: str
    access_mode: str
    is_enabled: bool
    health_status: Literal["unknown"]
    last_fetched_at: datetime | None


class SourcePatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_enabled: bool


class FeatureFlagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    description: str | None
    enabled: bool
    organization_ids: list[str] | None
    rollout_pct: int
    expires_at: datetime | None
    created_at: datetime


class FeatureFlagPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool | None = None
    organization_ids: list[str] | None = Field(default=None, max_length=1000)
    rollout_pct: int | None = Field(default=None, ge=0, le=100)
    expires_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def require_aware_expiry(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("expires_at must include a timezone")
        return value

    @model_validator(mode="after")
    def require_patch_field(self) -> FeatureFlagPatchRequest:
        if not self.model_fields_set:
            raise ValueError("At least one feature flag field must be provided")
        if "enabled" in self.model_fields_set and self.enabled is None:
            raise ValueError("enabled cannot be null")
        if "rollout_pct" in self.model_fields_set and self.rollout_pct is None:
            raise ValueError("rollout_pct cannot be null")
        return self


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str | None
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str
    details: dict[str, object] | None
    trace_id: str | None
    created_at: datetime


class UnmatchedListingResponse(BaseModel):
    id: str
    reference_id: str
    source_key: str
    title: str | None
    external_url: str | None
    match_method: str | None
    observation_at: datetime


class UnmatchedResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_id: str = Field(min_length=1, max_length=128)


class DuplicateGroupResponse(BaseModel):
    id: str
    representative_id: str
    method: str | None
    confidence: Decimal | None
    listing_ids: list[str]
    created_at: datetime
