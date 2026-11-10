from __future__ import annotations

import logging
from typing import Any

from apps.api.schemas import ApiError
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("chronoarb.api")


def _field_errors_from_exception(exc: Exception) -> dict[str, list[str]]:
    field_errors: dict[str, list[str]] = {}
    if isinstance(exc, (RequestValidationError, PydanticValidationError)):
        for error in exc.errors():
            loc = error.get("loc", ())
            key = ".".join(str(part) for part in loc if str(part) != "body") or "request"
            field_errors.setdefault(key, []).append(str(error.get("msg", "Invalid value.")))
    return field_errors


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    field_errors: dict[str, list[str]] | None = None,
    retryable: bool = False,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    payload = ApiError(
        code=code,
        message=message,
        field_errors=field_errors or {},
        trace_id=getattr(request.state, "trace_id", "unknown"),
        retryable=retryable,
    )
    return JSONResponse(
        status_code=status_code,
        content={"error": payload.model_dump()},
        headers=headers,
    )


async def pydantic_validation_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, PydanticValidationError):
        raise TypeError("Validation handler received an unsupported exception")
    field_errors = _field_errors_from_exception(exc)
    logger.warning(
        "validation_error",
        extra={"trace_id": getattr(request.state, "trace_id", "unknown"), "errors": field_errors},
    )
    return _error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="One or more fields are invalid.",
        field_errors=field_errors,
    )


async def request_validation_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise TypeError("Validation handler received an unsupported exception")
    field_errors = _field_errors_from_exception(exc)
    logger.warning(
        "validation_error",
        extra={"trace_id": getattr(request.state, "trace_id", "unknown"), "errors": field_errors},
    )
    return _error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="One or more fields are invalid.",
        field_errors=field_errors,
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise TypeError("HTTP exception handler received an unsupported exception")
    detail = exc.detail
    field_errors: dict[str, list[str]] = {}
    if isinstance(detail, dict):
        error_details = detail.get("field_errors")
        if isinstance(error_details, dict):
            field_errors = {
                str(key): [str(item) for item in values]
                for key, values in error_details.items()
                if isinstance(values, list)
            }
        message = str(detail.get("message") or detail.get("detail") or exc.detail)
    elif isinstance(detail, str):
        message = detail
    else:
        message = "The request could not be completed."

    if exc.status_code >= 500:
        code = "INTERNAL_ERROR"
        message = "An internal error occurred."
        retryable = True
    elif exc.status_code == 401:
        code = "UNAUTHORIZED"
        retryable = False
    elif exc.status_code == 403:
        code = "FORBIDDEN"
        retryable = False
    elif exc.status_code == 404:
        code = "NOT_FOUND"
        retryable = False
    elif exc.status_code == 409:
        code = "CONFLICT"
        retryable = False
    elif exc.status_code == 422:
        code = "VALIDATION_ERROR"
        retryable = False
    elif exc.status_code == 429:
        code = "RATE_LIMITED"
        retryable = True
    elif exc.status_code == 503:
        code = "SERVICE_UNAVAILABLE"
        retryable = True
    else:
        code = "REQUEST_ERROR"
        retryable = False

    response = _error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=message,
        field_errors=field_errors,
        retryable=retryable,
        headers=dict(exc.headers) if exc.headers else None,
    )
    return response


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error", extra={"trace_id": getattr(request.state, "trace_id", "unknown")})
    return _error_response(
        request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="An internal error occurred.",
        retryable=True,
    )
