from __future__ import annotations

import hashlib
import hmac
import time

import pytest
from apps.api.billing.api.router import verify_stripe_signature
from apps.api.infrastructure.models import Base
from apps.api.main import app
from apps.api.settings import settings
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with sessionmaker() as database_session:
        yield database_session
    await engine.dispose()


@pytest.fixture
async def client(session):
    from apps.api.infrastructure.database import get_db

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_db, None)


def test_stripe_signature_accepts_valid_recent_request(monkeypatch) -> None:
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")
    payload = b'{"id":"evt_1","type":"test","data":{}}'
    timestamp = str(int(time.time()))
    signed_payload = timestamp.encode("ascii") + b"." + payload
    signature = hmac.new(
        b"whsec_test",
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    assert verify_stripe_signature(payload, f"t={timestamp},v1={signature}")


def test_stripe_signature_rejects_missing_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "stripe_webhook_secret", "")
    assert verify_stripe_signature(b"{}", "t=1,v1=test") is False


async def test_opportunities_require_tenant_header(client) -> None:
    response = await client.get("/api/v1/opportunities")
    assert response.status_code == 422 or response.status_code == 401


async def test_billing_webhook_rejects_missing_signature(client) -> None:
    response = await client.post(
        "/api/v1/billing/stripe/webhook",
        content='{"id":"evt_1","type":"test","data":{}}',
    )
    assert response.status_code == 401


async def test_canonical_billing_webhook_rejects_missing_signature(client) -> None:
    response = await client.post(
        "/api/v1/billing/webhook",
        content='{"id":"evt_1","type":"test","data":{}}',
    )
    assert response.status_code == 401
