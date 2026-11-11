from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Channel3SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=256)
    limit: int = Field(default=20, ge=1, le=50)
    page_token: str | None = Field(default=None, min_length=1, max_length=2048)


class WatchListCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    reference_ids: list[str] = Field(default_factory=list, max_length=500)


class WatchListUpdateRequest(WatchListCreateRequest):
    pass


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    created_at: datetime


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_key: str
    display_name: str
    adapter_version: str
    access_mode: str
    is_enabled: bool
    created_at: datetime


class ReferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    brand_id: str
    ref_code: str
    model_name: str | None = None
    generation: str | None = None
    is_active: bool
    created_at: datetime


class ReferenceDetailResponse(ReferenceResponse):
    attributes: dict[str, object] | None = None
    aliases: list[str] = Field(default_factory=list)


class ReferencePageResponse(BaseModel):
    items: list[ReferenceResponse]
    next_cursor: str | None
    has_more: bool


class WatchListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    created_at: datetime
    entries: list[WatchListEntryResponse] = Field(default_factory=list)


class WatchListEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    watch_list_id: str
    reference_id: str
    created_at: datetime
