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
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "opportunity_demo_001",
                    "organization_id": "org_demo",
                    "listing_id": "listing_demo_001",
                    "valuation_id": "valuation_demo_001",
                    "material_version": 1,
                    "score": "0.92",
                    "state": "published",
                    "positive_factors": ["price_below_expected"],
                    "negative_factors": [],
                    "published_at": "2026-10-25T09:00:00Z",
                    "state_changed_at": "2026-10-25T09:00:00Z",
                    "created_at": "2026-10-25T09:00:00Z",
                    "data_age_seconds": 900,
                    "confidence": "0.87",
                    "valuation_version": "v1",
                    "cost_assumptions_version": "costs-2026-01",
                    "my_decision": None,
                    "listing": {
                        "id": "listing_demo_001",
                        "title": "Example automatic watch",
                        "description": "Example listing details.",
                        "external_url": "https://example.com/listing/001",
                        "listing_price": "1200.00",
                        "listing_price_currency": "USD",
                        "normalized_price": "1200.00",
                        "normalized_currency": "USD",
                        "condition": "very_good",
                        "set_status": "box_and_papers",
                        "seller_geography": "US",
                        "listed_at": "2026-10-25T08:45:00Z",
                        "reference_id": "ref_demo_001",
                        "brand_name": "Example",
                        "ref_code": "EX-001",
                        "model_name": "Example Automatic",
                        "generation": "1",
                        "reference_attributes": {},
                        "parsed_attributes": {},
                        "source_key": "approved_source",
                        "source_display_name": "Approved source",
                        "match_confidence": "0.96",
                        "match_method": "reference_match_v1",
                        "match_features": {},
                        "fx_rate": "1.00",
                        "fx_source": "example_fx",
                        "fx_date": "2026-10-25",
                    },
                    "valuation": {
                        "id": "valuation_demo_001",
                        "listing_id": "listing_demo_001",
                        "model_version": "valuation-v1",
                        "config_version": "config-2026-01",
                        "cost_assumptions_version": "costs-2026-01",
                        "expected_exit_price": "1500.00",
                        "exit_price_currency": "USD",
                        "all_in_acquisition": "1250.00",
                        "expected_net_resale": "1450.00",
                        "expected_net_profit": "200.00",
                        "roi": "0.16",
                        "low_estimate": "1400.00",
                        "high_estimate": "1600.00",
                        "confidence": "0.87",
                        "comparable_count": 12,
                        "sample_dispersion": "0.08",
                        "cost_breakdown": {},
                        "adjustment_details": {},
                        "risk_reserve_details": {},
                        "created_at": "2026-10-25T09:00:00Z",
                    },
                }
            ]
        },
    )

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
