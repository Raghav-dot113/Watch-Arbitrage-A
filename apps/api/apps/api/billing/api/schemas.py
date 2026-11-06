from __future__ import annotations

from pydantic import BaseModel


class StripeWebhookResponse(BaseModel):
    received: bool
    event_id: str
    replayed: bool
