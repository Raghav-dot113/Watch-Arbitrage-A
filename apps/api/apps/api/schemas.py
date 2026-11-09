from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    trace_id: str


class ReadyResponse(BaseModel):
    status: str
    database: str
    trace_id: str


class ApiError(BaseModel):
    code: str
    message: str
    field_errors: dict[str, list[str]] = Field(default_factory=dict)
    trace_id: str
    retryable: bool = False


class ApiErrorResponse(BaseModel):
    error: ApiError


class ApiMeta(BaseModel):
    trace_id: str
    next_cursor: str | None = None
    has_more: bool = False


class ApiSuccessEnvelope[DataT](BaseModel):
    data: DataT
    meta: ApiMeta
