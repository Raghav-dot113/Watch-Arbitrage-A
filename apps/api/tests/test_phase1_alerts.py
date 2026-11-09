from __future__ import annotations

from datetime import UTC, datetime

import pytest
from apps.api.alerts.infrastructure.models import AlertRule
from apps.api.identity.api.context import OrganizationContext, get_organization_context
from apps.api.identity.infrastructure.models import Organization, User
from apps.api.infrastructure.database import get_db
from apps.api.infrastructure.models import Base
from apps.api.main import app
from apps.api.operations.infrastructure.models import AuditEvent
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chronoarb.domain.ulid import generate_ulid


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
    organization = Organization(
        id=generate_ulid("org"),
        name="Dealer organization",
        slug="dealer-org",
        created_at=datetime.now(UTC),
    )
    user = User(
        id=generate_ulid("usr"),
        cognito_sub="dealer-subject",
        email="dealer@example.com",
        display_name="Dealer",
    )
    session.add_all([organization, user])
    await session.commit()

    active_context = OrganizationContext(
        organization_id=organization.id,
        user_id=user.id,
        role="dealer",
    )

    async def override_get_db():
        yield session

    async def override_context() -> OrganizationContext:
        return active_context

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_organization_context] = override_context
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client, session, active_context
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_organization_context, None)


async def test_dealer_can_create_alert_and_idempotent_replay_is_stable(client) -> None:
    test_client, session, context = client
    payload = {
        "name": "Submariner alerts",
        "filters": {"brand_id": "brd_test"},
        "channels": {"telegram": True},
        "cooldown_minutes": 60,
        "is_enabled": True,
    }

    first = await test_client.post(
        "/api/v1/alerts/rules",
        json=payload,
        headers={"Idempotency-Key": "idem-alert-1"},
    )
    replay = await test_client.post(
        "/api/v1/alerts/rules",
        json=payload,
        headers={"Idempotency-Key": "idem-alert-1"},
    )
    mismatch = await test_client.post(
        "/api/v1/alerts/rules",
        json={**payload, "name": "Different request"},
        headers={"Idempotency-Key": "idem-alert-1"},
    )
    listing = await test_client.get("/api/v1/alerts/rules?limit=1")

    assert first.status_code == 201
    assert first.json()["data"]["organization_id"] == context.organization_id
    assert set(first.json()["meta"]) == {"trace_id", "next_cursor", "has_more"}
    assert replay.status_code == 200
    assert replay.json()["data"] == first.json()["data"]
    assert mismatch.status_code == 422
    assert listing.status_code == 200
    assert listing.json()["data"][0]["id"] == first.json()["data"]["id"]
    assert set(listing.json()["meta"]) == {"trace_id", "next_cursor", "has_more"}
    assert await session.scalar(select(func.count()).select_from(AlertRule)) == 1
    assert await session.scalar(select(func.count()).select_from(AuditEvent)) == 1


async def test_viewer_cannot_create_alert(client) -> None:
    test_client = client[0]
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id="org_viewer",
        user_id="usr_viewer",
        role="viewer",
    )

    response = await test_client.post(
        "/api/v1/alerts/rules",
        json={"name": "Denied", "filters": {}, "channels": {}},
        headers={"Idempotency-Key": "idem-alert-viewer"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
