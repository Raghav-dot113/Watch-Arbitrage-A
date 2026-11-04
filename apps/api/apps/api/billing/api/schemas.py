from __future__ import annotations

from datetime import datetime
from typing import Literal

from apps.api.billing.domain import SubscriptionStatus
from pydantic import BaseModel, ConfigDict, Field


class StripeCheckoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")


class StripeSessionResponse(BaseModel):
    session_id: str
    url: str


class StripePortalResponse(BaseModel):
    url: str


class StripeWebhookResponse(BaseModel):
    received: Literal[True] = True
    duplicate: bool = False


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None
    status: SubscriptionStatus
    plan_id: str | None
    current_period_start: datetime | None
    current_period_end: datetime | None
    trial_end: datetime | None
