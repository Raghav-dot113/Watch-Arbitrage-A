from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str = Field(pattern="^(purchased|contacted|dismissed)$")
    notes: str | None = Field(default=None, max_length=2000)


class LegacyFeedbackRequest(FeedbackRequest):
    opportunity_id: str = Field(min_length=1)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=128)


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    decision: str
    notes: str | None
    created_at: datetime
