from __future__ import annotations

import pytest
from apps.api.middleware.error_handler import register_api_error_handlers
from apps.api.middleware.tracing import TraceIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient


def _create_error_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)
    register_api_error_handlers(app)

    @app.get("/errors/401")
    async def unauthorized() -> None:
        raise HTTPException(status_code=401, detail="Authentication required.")

    @app.get("/errors/403")
    async def forbidden() -> None:
        raise HTTPException(status_code=403, detail="Insufficient permission.")

    @app.get("/errors/409")
    async def conflict() -> None:
        raise HTTPException(status_code=409, detail="Conflict.")

    @app.get("/errors/429")
    async def rate_limited() -> None:
        raise HTTPException(status_code=429, detail="Slow down.")

    @app.get("/errors/503")
    async def unavailable() -> None:
        raise HTTPException(status_code=503, detail="Unavailable.")

    @app.get("/errors/custom")
    async def custom_error() -> None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "not_configured",
                "message": "Search provider is not configured.",
                "retryable": False,
            },
        )

    @app.get("/errors/500")
    async def internal_error() -> None:
        raise RuntimeError("internal detail must not be returned")

    @app.get("/errors/method")
    async def method_error() -> JSONResponse:
        return JSONResponse({"ok": True})

    @app.get("/validate")
    async def validate(value: int) -> dict[str, int]:
        return {"value": value}

    return app


@pytest.mark.parametrize(
    ("method", "path", "status_code", "error_code", "retryable"),
    [
        ("GET", "/errors/401", 401, "UNAUTHORIZED", False),
        ("GET", "/errors/403", 403, "FORBIDDEN", False),
        ("GET", "/missing", 404, "NOT_FOUND", False),
        ("POST", "/errors/method", 405, "METHOD_NOT_ALLOWED", False),
        ("GET", "/errors/409", 409, "CONFLICT", False),
        ("GET", "/validate?value=invalid", 422, "VALIDATION_ERROR", False),
        ("GET", "/errors/429", 429, "RATE_LIMITED", True),
        ("GET", "/errors/503", 503, "SERVICE_UNAVAILABLE", True),
        ("GET", "/errors/500", 500, "INTERNAL_ERROR", True),
    ],
)
async def test_error_responses_use_the_api_envelope(
    method: str,
    path: str,
    status_code: int,
    error_code: str,
    retryable: bool,
) -> None:
    transport = ASGITransport(app=_create_error_app(), raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request(
            method,
            path,
            headers={"X-Trace-Id": "trc_contract_test"},
        )

    assert response.status_code == status_code
    error = response.json()["error"]
    assert set(error) == {"code", "message", "field_errors", "trace_id", "retryable"}
    assert error["code"] == error_code
    assert error["trace_id"] == "trc_contract_test"
    assert error["retryable"] is retryable


async def test_validation_envelope_includes_field_errors() -> None:
    transport = ASGITransport(app=_create_error_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/validate?value=invalid")

    assert response.status_code == 422
    assert response.json()["error"]["field_errors"]["query.value"]


async def test_http_exception_preserves_explicit_error_code_and_retryability() -> None:
    transport = ASGITransport(app=_create_error_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/errors/custom")

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "not_configured",
        "message": "Search provider is not configured.",
        "field_errors": {},
        "trace_id": response.json()["error"]["trace_id"],
        "retryable": False,
    }
