from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StripeWebhookResponse(BaseModel):
    received: bool
    event_id: str
    replayed: bool


class StripeEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    type: str
    data: dict[str, object]
