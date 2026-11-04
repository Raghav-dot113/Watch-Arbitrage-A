from __future__ import annotations

import logging

from apps.api.infrastructure.http_status import HTTP_422_UNPROCESSABLE_ENTITY
from apps.api.schemas import ApiError
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)

logger = logging.getLogger("chronoarb.api")
_HTTP_422 = HTTP_422_UNPROCESSABLE_ENTITY

_HTTP_ERROR_DETAILS: dict[int, tuple[str, str, bool]] = {
    HTTP_401_UNAUTHORIZED: ("UNAUTHORIZED", "Authentication is required.", False),
    HTTP_403_FORBIDDEN: ("FORBIDDEN", "You do not have permission to perform this action.", False),
    HTTP_404_NOT_FOUND: ("NOT_FOUND", "The requested resource was not found.", False),
    HTTP_409_CONFLICT: (
        "CONFLICT",
        "The request conflicts with the current resource state.",
        False,
    ),
    _HTTP_422: ("VALIDATION_ERROR", "One or more fields are invalid.", False),
    HTTP_429_TOO_MANY_REQUESTS: ("RATE_LIMITED", "Too many requests.", True),
    HTTP_500_INTERNAL_SERVER_ERROR: (
        "INTERNAL_ERROR",
        "An internal error occurred.",
        True,
    ),
    HTTP_503_SERVICE_UNAVAILABLE: (
        "SERVICE_UNAVAILABLE",
        "The service is temporarily unavailable.",
        True,
    ),
}


async def pydantic_validation_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, (RequestValidationError, PydanticValidationError)):
        raise TypeError("Validation handler received an unsupported exception")
    trace_id = getattr(request.state, "trace_id", "unknown")
    field_errors: dict[str, list[str]] = {}
    for error in exc.errors():
        loc = ".".join(str(p) for p in error["loc"])
        msg = error["msg"]
        field_errors.setdefault(loc, []).append(msg)

    api_error = ApiError(
        code="VALIDATION_ERROR",
        message="One or more fields are invalid.",
        field_errors=field_errors,
        trace_id=trace_id,
        retryable=False,
    )
    logger.warning("validation_error", extra={"trace_id": trace_id, "errors": field_errors})
    return JSONResponse(
        status_code=_HTTP_422,
        content={"error": api_error.model_dump()},
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise TypeError("HTTP handler received an unsupported exception")
    trace_id = getattr(request.state, "trace_id", "unknown")
    code, message, retryable = _HTTP_ERROR_DETAILS.get(
        exc.status_code,
        ("REQUEST_ERROR", "The request could not be completed.", False),
    )
    field_errors = None
    if exc.status_code == _HTTP_422 and isinstance(exc.detail, str):
        field_errors = {"request": [exc.detail]}
    api_error = ApiError(
        code=code,
        message=message,
        field_errors=field_errors,
        trace_id=trace_id,
        retryable=retryable,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": api_error.model_dump()},
        headers=exc.headers,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.exception("unhandled_error", extra={"trace_id": trace_id})
    api_error = ApiError(
        code="INTERNAL_ERROR",
        message="An internal error occurred.",
        trace_id=trace_id,
        retryable=True,
    )
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": api_error.model_dump()},
    )
