from __future__ import annotations

from typing import Any

from apps.api.schemas import ApiSuccessEnvelope
from fastapi.responses import JSONResponse


def success_payload(
    data: Any,
    trace_id: str,
    *,
    next_cursor: str | None = None,
    has_more: bool = False,
) -> dict[str, Any]:
    envelope = ApiSuccessEnvelope[Any](
        data=data,
        meta={
            "trace_id": trace_id,
            "next_cursor": next_cursor,
            "has_more": has_more,
        },
    )
    return envelope.model_dump(mode="json")


def success_response(
    data: Any,
    trace_id: str,
    *,
    next_cursor: str | None = None,
    has_more: bool = False,
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=success_payload(
            data,
            trace_id,
            next_cursor=next_cursor,
            has_more=has_more,
        ),
    )
