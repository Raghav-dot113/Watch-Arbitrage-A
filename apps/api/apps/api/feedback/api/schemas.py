from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

FeedbackDecision = Literal["purchased", "contacted", "dismissed"]
CurrencyCode = str


def _require_money_string(value: object) -> object:
    if not isinstance(value, str):
        raise ValueError("Money values must be decimal strings")
    return value


MoneyInput = Annotated[Decimal, BeforeValidator(_require_money_string)]


class FeedbackCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    decision: FeedbackDecision
    notes: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    user_id: str
    opportunity_id: str
    decision: FeedbackDecision
    notes: str | None
    created_at: datetime


class FeedbackCreateResponse(BaseModel):
    feedback: FeedbackResponse
    opportunity_state: str


class OpportunityHistoryValuationResponse(BaseModel):
    id: str
    model_version: str
    cost_assumptions_version: str
    expected_exit_price: Decimal | None
    exit_price_currency: str | None
    expected_net_profit: Decimal | None
    roi: Decimal | None
    confidence: Decimal | None


class OpportunityHistoryItemResponse(BaseModel):
    id: str
    listing_id: str
    material_version: int
    state: str
    score: Decimal | None
    published_at: datetime | None
    state_changed_at: datetime | None
    created_at: datetime
    valuation: OpportunityHistoryValuationResponse


class TradeOutcomeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acquisition_price: MoneyInput | None = Field(
        default=None, ge=0, max_digits=18, decimal_places=2
    )
    acquisition_currency: CurrencyCode | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    resale_price: MoneyInput | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    resale_currency: CurrencyCode | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    actual_profit: MoneyInput | None = Field(
        default=None,
        max_digits=18,
        decimal_places=2,
        description="Dealer-reported profit denominated in acquisition_currency.",
    )
    days_to_sell: int | None = Field(default=None, ge=0, le=36500)

    @model_validator(mode="after")
    def validate_outcome_fields(self) -> TradeOutcomeCreateRequest:
        if (self.acquisition_price is None) != (self.acquisition_currency is None):
            raise ValueError("acquisition_price and acquisition_currency must be provided together")
        if (self.resale_price is None) != (self.resale_currency is None):
            raise ValueError("resale_price and resale_currency must be provided together")
        if all(
            value is None
            for value in (
                self.acquisition_price,
                self.resale_price,
                self.actual_profit,
                self.days_to_sell,
            )
        ):
            raise ValueError("At least one trade outcome value must be provided")
        if self.actual_profit is not None and self.acquisition_currency is None:
            raise ValueError("actual_profit requires acquisition_price and acquisition_currency")
        return self


class TradeOutcomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    user_id: str
    opportunity_id: str | None
    reference_id: str
    acquisition_price: Decimal | None
    acquisition_currency: CurrencyCode | None
    resale_price: Decimal | None
    resale_currency: CurrencyCode | None
    actual_profit: Decimal | None
    actual_profit_currency: CurrencyCode | None
    days_to_sell: int | None
    created_at: datetime


class ActivityItemResponse(BaseModel):
    id: str
    event_type: Literal["feedback", "outcome"]
    user_id: str
    opportunity_id: str | None
    reference_id: str | None
    decision: FeedbackDecision | None
    notes: str | None
    acquisition_price: Decimal | None
    acquisition_currency: CurrencyCode | None
    resale_price: Decimal | None
    resale_currency: CurrencyCode | None
    actual_profit: Decimal | None
    days_to_sell: int | None
    created_at: datetime
