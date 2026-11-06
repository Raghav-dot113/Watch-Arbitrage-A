from __future__ import annotations

from apps.api.schemas import HealthResponse
from fastapi import Request
from fastapi.responses import JSONResponse


async def health_handler(request: Request) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", "unknown")
    return JSONResponse(
        content={"data": HealthResponse(status="ok", trace_id=trace_id).model_dump()}
    )
