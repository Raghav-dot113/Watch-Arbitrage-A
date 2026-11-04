from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

OpportunityState = Literal["published", "dismissed", "contacted", "purchased", "expired"]


class OpportunityListingResponse(BaseModel):
    id: str
    title: str
    description: str | None
    external_url: str | None
    listing_price: Decimal | None
    listing_price_currency: str | None
    normalized_price: Decimal | None
    normalized_currency: str | None
    condition: str | None
    set_status: str | None
    seller_geography: str | None
    listed_at: datetime | None
    reference_id: str
    brand_name: str
    ref_code: str
    model_name: str | None
    generation: str | None
    reference_attributes: dict[str, object] | None
    parsed_attributes: dict[str, object] | None
    source_key: str
    source_display_name: str
    match_confidence: Decimal | None
    match_method: str | None
    match_features: dict[str, object] | None
    fx_rate: Decimal
    fx_source: str
    fx_date: date


class OpportunityValuationResponse(BaseModel):
    id: str
    listing_id: str
    model_version: str
    config_version: str
    cost_assumptions_version: str
    expected_exit_price: Decimal | None
    exit_price_currency: str | None
    all_in_acquisition: Decimal | None
    expected_net_resale: Decimal | None
    expected_net_profit: Decimal | None
    roi: Decimal | None
    low_estimate: Decimal | None
    high_estimate: Decimal | None
    confidence: Decimal | None
    comparable_count: int | None
    sample_dispersion: Decimal | None
    cost_breakdown: dict[str, object] | None
    adjustment_details: dict[str, object] | None
    risk_reserve_details: dict[str, object] | None
    created_at: datetime


class OpportunityFeedItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    listing_id: str
    valuation_id: str
    material_version: int
    score: Decimal | None
    state: OpportunityState
    positive_factors: dict[str, object] | list[object] | None
    negative_factors: dict[str, object] | list[object] | None
    published_at: datetime | None
    state_changed_at: datetime | None
    created_at: datetime
    data_age_seconds: int
    confidence: Decimal | None
    valuation_version: str
    cost_assumptions_version: str
    my_decision: str | None
    listing: OpportunityListingResponse
    valuation: OpportunityValuationResponse


class OpportunityDetailResponse(OpportunityFeedItem):
    observation_at: datetime
