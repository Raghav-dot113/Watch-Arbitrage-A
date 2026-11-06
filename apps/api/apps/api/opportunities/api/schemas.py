from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class OpportunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    listing_id: str
    valuation_id: str
    material_version: int
    score: Decimal | None
    state: str
    positive_factors: dict[str, Any] | list[Any] | None = None
    negative_factors: dict[str, Any] | list[Any] | None = None
    published_at: datetime | None
    created_at: datetime


class OpportunityListResponse(BaseModel):
    data: list[OpportunityResponse]
    meta: dict[str, Any]
