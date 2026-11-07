from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

import pytest
from apps.api.identity.infrastructure import models as _identity_models  # noqa: F401
from apps.api.infrastructure.idempotency import (
    make_idempotency_identity,
    require_idempotency_key,
    validate_idempotency_key,
)
from apps.api.infrastructure.models import Base
from apps.api.main import create_app
from apps.api.operations.application.audit import record_audit_event
from apps.api.operations.infrastructure.models import AuditEvent
from apps.api.settings import Settings, settings
from fastapi import Depends, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class RequestPayload(BaseModel):
    count: int


@pytest.fixture
async def audit_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite://")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def b08_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    monkeypatch.setattr(settings, "cors_origins", "http://localhost:3000")
    application = create_app()

    @application.post("/test-validation")
    async def validate_payload(payload: RequestPayload) -> dict[str, int]:
        return {"count": payload.count}

    @application.get("/test-http-error")
    async def raise_http_error() -> None:
        raise HTTPException(
            status_code=401,
            detail="private implementation detail",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @application.get("/test-server-error")
    async def raise_server_error() -> None:
        raise RuntimeError("private implementation detail")

    @application.post("/test-idempotency")
    async def use_idempotency_key(
        key: Annotated[str, Depends(require_idempotency_key)],
    ) -> dict[str, str]:
        return {"key": key}

    transport = ASGITransport(app=application, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_request_validation_uses_stable_error_envelope(b08_client: AsyncClient) -> None:
    response = await b08_client.post("/test-validation", json={"count": "invalid"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["message"] == "One or more fields are invalid."
    assert error["field_errors"]["body.count"]
    assert error["trace_id"] == response.headers["X-Trace-Id"]
    assert error["retryable"] is False


async def test_http_exceptions_use_envelope_without_leaking_details(
    b08_client: AsyncClient,
) -> None:
    response = await b08_client.get("/test-http-error")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert "private implementation detail" not in response.text


async def test_unexpected_exceptions_use_generic_error_envelope(
    b08_client: AsyncClient,
) -> None:
    response = await b08_client.get("/test-server-error")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.json()["error"]["retryable"] is True
    assert "private implementation detail" not in response.text


async def test_cors_preflight_allows_configured_origin_and_headers(
    b08_client: AsyncClient,
) -> None:
    response = await b08_client.options(
        "/api/v1/test",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,idempotency-key",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "idempotency-key" in response.headers["access-control-allow-headers"].lower()
    assert "X-Trace-Id" in response.headers
    cors_get = await b08_client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert cors_get.headers["access-control-expose-headers"] == "X-Trace-Id"


async def test_cors_rejects_unconfigured_origin(b08_client: AsyncClient) -> None:
    response = await b08_client.get(
        "/health",
        headers={"Origin": "https://untrusted.example"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_settings_validate_explicit_cors_origins() -> None:
    configured = Settings(
        _env_file=None,
        cors_origins="http://localhost:3000/,https://chronoarb.example",
    )
    assert configured.cors_origin_allowlist == (
        "http://localhost:3000",
        "https://chronoarb.example",
    )

    for invalid_origins in (
        "*",
        "https://chronoarb.example/path",
        "https://user:password@chronoarb.example",
        "https://chronoarb.example,,https://other.example",
    ):
        with pytest.raises(ValueError, match=r"Invalid CORS origin|comma-separated"):
            Settings(_env_file=None, cors_origins=invalid_origins)


async def test_idempotency_dependency_requires_valid_client_key(
    b08_client: AsyncClient,
) -> None:
    missing = await b08_client.post("/test-idempotency")
    valid = await b08_client.post(
        "/test-idempotency",
        headers={"Idempotency-Key": "idem_client-123"},
    )

    assert missing.status_code == 422
    assert missing.json()["error"]["field_errors"]["request"]
    assert valid.status_code == 200
    assert valid.json() == {"key": "idem_client-123"}


@pytest.mark.parametrize("value", ["", "has space", "line\nbreak", "é", "x" * 256])
def test_idempotency_key_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match="printable ASCII"):
        validate_idempotency_key(value)


def test_idempotency_identity_is_scoped_and_payload_fingerprinted() -> None:
    identity = make_idempotency_identity(
        key="same-key",
        organization_id="org_one",
        user_id="usr_one",
        operation="feedback.create",
        payload={"decision": "purchased", "note": "Bought"},
    )
    same_request = make_idempotency_identity(
        key="same-key",
        organization_id="org_one",
        user_id="usr_one",
        operation="feedback.create",
        payload={"note": "Bought", "decision": "purchased"},
    )
    different_payload = make_idempotency_identity(
        key="same-key",
        organization_id="org_one",
        user_id="usr_one",
        operation="feedback.create",
        payload={"decision": "dismissed", "note": "Bought"},
    )
    different_tenant = make_idempotency_identity(
        key="same-key",
        organization_id="org_two",
        user_id="usr_one",
        operation="feedback.create",
        payload={"decision": "purchased", "note": "Bought"},
    )

    assert identity == same_request
    assert identity.request_fingerprint != different_payload.request_fingerprint
    assert identity.storage_key != different_tenant.storage_key
    assert "same-key" not in identity.storage_key


async def test_audit_helper_flushes_without_committing(audit_session: AsyncSession) -> None:
    event = await record_audit_event(
        audit_session,
        organization_id=None,
        user_id=None,
        action="source.enabled",
        resource_type="source",
        resource_id="src_01",
        details={"enabled": True},
        trace_id="trc_01",
        client_ip="127.0.0.1",
    )

    assert event.id.startswith("aud_")
    assert event.action == "source.enabled"
    assert event.details == {"enabled": True}
    assert event.trace_id == "trc_01"
    assert audit_session.in_transaction()
    await audit_session.rollback()
    assert (
        await audit_session.execute(select(AuditEvent).where(AuditEvent.id == event.id))
    ).scalar_one_or_none() is None


async def test_audit_helper_rejects_empty_action_fields(audit_session: AsyncSession) -> None:
    with pytest.raises(ValueError, match="action"):
        await record_audit_event(
            audit_session,
            action=" ",
            resource_type="organization",
            resource_id="org_01",
        )


async def test_audit_helper_requires_valid_foreign_keys(audit_session: AsyncSession) -> None:
    with pytest.raises(IntegrityError):
        await record_audit_event(
            audit_session,
            organization_id="org_missing",
            user_id="usr_missing",
            action="member.role_changed",
            resource_type="membership",
            resource_id="mem_missing",
        )
