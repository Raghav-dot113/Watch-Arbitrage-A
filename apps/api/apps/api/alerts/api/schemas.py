from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AlertRuleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    filters: dict[str, Any] = Field(default_factory=dict)
    channels: dict[str, Any] = Field(default_factory=dict)
    cooldown_minutes: int = Field(default=60, ge=1, le=10080)
    is_enabled: bool = True


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    filters: dict[str, Any]
    channels: dict[str, Any]
    cooldown_minutes: int
    is_enabled: bool
    created_at: datetime
