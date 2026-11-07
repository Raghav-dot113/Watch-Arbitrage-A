from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
)

AlertChannel = Literal["in_app", "push", "telegram"]
DeliveryStatus = Literal["pending", "sent", "failed", "suppressed"]


def _decimal_string(value: object) -> object:
    if not isinstance(value, str):
        raise ValueError("Money filters must be decimal strings")
    return value


DecimalFilter = Annotated[Decimal, BeforeValidator(_decimal_string)]


class AlertRuleFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_ids: list[str] | None = Field(default=None, max_length=50)
    min_profit: DecimalFilter | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    max_acquisition: DecimalFilter | None = Field(
        default=None, ge=0, max_digits=18, decimal_places=2
    )
    conditions: list[str] | None = Field(default=None, max_length=20)

    @field_validator("reference_ids", "conditions")
    @classmethod
    def require_unique_nonempty_values(cls, values: list[str] | None) -> list[str] | None:
        if values is not None and (
            any(not value.strip() for value in values) or len(values) != len(set(values))
        ):
            raise ValueError("Filter values must be nonempty and unique")
        return values


class AlertRuleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    filters: AlertRuleFilters = Field(default_factory=AlertRuleFilters)
    channels: list[AlertChannel] = Field(min_length=1, max_length=3)
    cooldown_minutes: int = Field(default=60, ge=1, le=10080)
    is_enabled: bool = True

    @field_validator("channels")
    @classmethod
    def require_unique_channels(cls, values: list[AlertChannel]) -> list[AlertChannel]:
        if len(values) != len(set(values)):
            raise ValueError("Alert channels must be unique")
        return values


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    created_by: str
    name: str
    filters: AlertRuleFilters
    channels: list[AlertChannel]
    cooldown_minutes: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class AlertDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rule_id: str
    opportunity_id: str
    material_version: int
    channel: str
    delivery_status: DeliveryStatus
    created_at: datetime


class AlertTestAcceptedResponse(BaseModel):
    event_id: str
    status: Literal["pending"]
