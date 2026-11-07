from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator


def _decimal_string(value: object) -> object:
    if not isinstance(value, str):
        raise ValueError("Money values must be decimal strings")
    return value


FeeAmount = Annotated[
    Decimal,
    BeforeValidator(_decimal_string),
    Field(ge=0, max_digits=18, decimal_places=2),
]


class FeeDefaults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    buyer_fee: FeeAmount | None = None
    tax_and_duty: FeeAmount | None = None
    inbound_shipping: FeeAmount | None = None
    authentication_cost: FeeAmount | None = None
    service_reserve: FeeAmount | None = None
    financing_cost: FeeAmount | None = None
    acquisition_risk_reserve: FeeAmount | None = None
    selling_fee: FeeAmount | None = None
    outbound_shipping: FeeAmount | None = None
    resale_payment_cost: FeeAmount | None = None
    exit_risk_reserve: FeeAmount | None = None


class OrganizationSettingsPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    default_fees: FeeDefaults | None = None

    @field_validator("currency", "timezone")
    @classmethod
    def require_non_null_settings(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("currency and timezone cannot be null")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is not None:
            try:
                ZoneInfo(value)
            except (ValueError, ZoneInfoNotFoundError) as error:
                raise ValueError("timezone must be a valid IANA time zone") from error
        return value

    @model_validator(mode="after")
    def require_patch_value(self) -> OrganizationSettingsPatchRequest:
        if not self.model_fields_set:
            raise ValueError("At least one settings field must be provided")
        return self


class OrganizationSettingsResponse(BaseModel):
    currency: str
    timezone: str
    default_fees: FeeDefaults
