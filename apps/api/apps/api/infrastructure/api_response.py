from __future__ import annotations

from typing import Any

from fastapi import Request
from pydantic import BaseModel


class ResponseMeta(BaseModel):
    trace_id: str
    next_cursor: str | None = None
    has_more: bool | None = None


class SuccessEnvelope[DataT](BaseModel):
    data: DataT
    meta: ResponseMeta


def success_response(
    request: Request,
    data: Any,
    *,
    next_cursor: str | None = None,
    has_more: bool | None = False,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "trace_id": getattr(request.state, "trace_id", "unknown"),
        "next_cursor": next_cursor if next_cursor is not None else "",
        "has_more": bool(has_more),
    }
    return {"data": data, "meta": meta}
