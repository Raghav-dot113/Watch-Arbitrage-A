from __future__ import annotations

import logging
from http import HTTPStatus

from apps.api.schemas import ApiError
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("chronoarb.api")
_OPERATIONAL_PATHS = frozenset({"/health", "/ready"})
_ERROR_CODES = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    503: "SERVICE_UNAVAILABLE",
}
_RETRYABLE_CODES = frozenset({"RATE_LIMITED", "SERVICE_UNAVAILABLE", "INTERNAL_ERROR"})


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    field_errors: dict[str, list[str]] | None = None,
) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", "unknown")
    error = ApiError(
        code=code,
        message=message,
        field_errors=field_errors or {},
        trace_id=trace_id,
        retryable=code in _RETRYABLE_CODES,
    )
    return JSONResponse(
        status_code=status_code,
        content={"error": error.model_dump()},
    )


def _validation_field_errors(errors: list[dict[str, object]]) -> dict[str, list[str]]:
    field_errors: dict[str, list[str]] = {}
    for error in errors:
        location = error.get("loc", ())
        if isinstance(location, (tuple, list)):
            key = ".".join(str(part) for part in location)
        else:
            key = ""
        message = error.get("msg", "Invalid value.")
        field_errors.setdefault(key, []).append(str(message))
    return field_errors


async def pydantic_validation_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    field_errors = _validation_field_errors(exc.errors())
    logger.warning(
        "validation_error",
        extra={"trace_id": getattr(request.state, "trace_id", "unknown"), "errors": field_errors},
    )
    return error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="One or more fields are invalid.",
        field_errors=field_errors,
    )


async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    field_errors = _validation_field_errors(exc.errors())
    logger.warning(
        "validation_error",
        extra={"trace_id": getattr(request.state, "trace_id", "unknown"), "errors": field_errors},
    )
    return error_response(
        request,
        status_code=422,
        code="VALIDATION_ERROR",
        message="One or more fields are invalid.",
        field_errors=field_errors,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    status_code = exc.status_code
    detail = exc.detail
    field_errors: dict[str, list[str]] = {}
    try:
        message = HTTPStatus(status_code).phrase
    except ValueError:
        message = "Request failed."

    if isinstance(detail, str):
        message = detail
    elif isinstance(detail, dict):
        message_value = detail.get("message")
        if isinstance(message_value, str):
            message = message_value
        errors_value = detail.get("field_errors")
        if isinstance(errors_value, dict):
            field_errors = {
                str(field): [str(item) for item in values]
                for field, values in errors_value.items()
                if isinstance(values, list)
            }

    if status_code >= 500:
        message = "An internal error occurred."
    code = _ERROR_CODES.get(status_code, "INTERNAL_ERROR" if status_code >= 500 else "HTTP_ERROR")

    if request.url.path in _OPERATIONAL_PATHS:
        return JSONResponse(
            status_code=status_code,
            content={"detail": message},
            headers=exc.headers,
        )

    response = error_response(
        request,
        status_code=status_code,
        code=code,
        message=message,
        field_errors=field_errors,
    )
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", "unknown")

    logger.exception(
        "unhandled_error",
        extra={"trace_id": trace_id},
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    if request.url.path in _OPERATIONAL_PATHS:
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    return error_response(
        request,
        status_code=500,
        code="INTERNAL_ERROR",
        message="An internal error occurred.",
    )


def register_api_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
