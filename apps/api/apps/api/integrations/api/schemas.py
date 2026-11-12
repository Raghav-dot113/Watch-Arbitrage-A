from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PushDeviceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: Literal["ios", "android"]
    device_token: str = Field(min_length=20, max_length=4096)


class PushDeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: Literal["ios", "android"]
    created_at: datetime
    updated_at: datetime


class IntegrationStatusResponse(BaseModel):
    telegram_status: Literal["disconnected", "pending", "connected"]
    telegram_link_expires_at: datetime | None
    push_devices: list[PushDeviceResponse]


class TelegramLinkResponse(BaseModel):
    link_url: str
    expires_at: datetime | None = None
    status: Literal["disconnected", "pending", "connected"] = "pending"


class TelegramConnectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_id: str = Field(min_length=1, max_length=128)


class TelegramTestResponse(BaseModel):
    delivered: bool
    chat_id: str
    provider_message_id: str | None = None
    error_message: str | None = None
