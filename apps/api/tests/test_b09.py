from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from apps.api.catalog.application.channel3 import (
    Channel3Offer,
    Channel3Price,
    Channel3Product,
    Channel3SearchResponse,
    Channel3UnavailableError,
)
from apps.api.catalog.infrastructure.channel3_client import Channel3Client
from apps.api.catalog.infrastructure.models import Brand, Reference, WatchList
from apps.api.identity.api.auth import issue_dev_token
from apps.api.identity.infrastructure.models import Membership, Organization, User
from apps.api.infrastructure.database import get_db
from apps.api.infrastructure.models import Base
from apps.api.main import create_app
from apps.api.settings import settings
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chronoarb.domain.ulid import generate_ulid

_SECRET = "test-only-authentication-secret-32-bytes-minimum"
_SUBJECT = "b09-user"
_ORG_ID = "org_b09_primary"
_OTHER_ORG_ID = "org_b09_other"


@pytest.fixture
async def b09_client(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[tuple[AsyncClient, async_sessionmaker[AsyncSession]]]:
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "auth_mode", "dev")
    monkeypatch.setattr(settings, "dev_jwt_secret", SecretStr(_SECRET))
    monkeypatch.setattr(settings, "jwt_issuer", "chronoarb-dev")
    monkeypatch.setattr(settings, "jwt_audience", "chronoarb-api")
    monkeypatch.setattr(settings, "platform_ops_subjects", "")

    engine = create_async_engine("sqlite+aiosqlite://")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    async with session_factory() as session:
        user = User(
            id="usr_b09_user",
            cognito_sub=_SUBJECT,
            email="b09@example.test",
            display_name="B09 Tester",
        )
        org = Organization(id=_ORG_ID, name="Primary", slug="b09-primary")
        other_org = Organization(id=_OTHER_ORG_ID, name="Other", slug="b09-other")
        viewer = User(
            id="usr_b09_viewer",
            cognito_sub="b09-viewer",
            email="viewer@example.test",
            display_name="B09 Viewer",
        )
        brand = Brand(id=generate_ulid("brd"), name="Rolex", slug="rolex")
        reference_one = Reference(
            id=generate_ulid("ref"),
            brand_id=brand.id,
            ref_code="126710",
            model_name="GMT-Master II",
        )
        reference_two = Reference(
            id=generate_ulid("ref"),
            brand_id=brand.id,
            ref_code="124060",
            model_name="Submariner",
        )
        session.add_all([user, org, other_org, viewer, brand])
        await session.flush()
        session.add_all(
            [
                Membership(
                    id="mem_b09_primary",
                    organization_id=org.id,
                    user_id=user.id,
                    role="owner",
                ),
                Membership(
                    id="mem_b09_other",
                    organization_id=other_org.id,
                    user_id=user.id,
                    role="dealer",
                ),
                Membership(
                    id="mem_b09_viewer",
                    organization_id=org.id,
                    user_id=viewer.id,
                    role="viewer",
                ),
                reference_one,
                reference_two,
                WatchList(
                    id="wl_b09_other",
                    organization_id=other_org.id,
                    name="Private other list",
                ),
            ]
        )
        await session.commit()

    headers = {
        "Authorization": f"Bearer {issue_dev_token(_SUBJECT)}",
        "X-Organization-ID": _ORG_ID,
    }
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.headers.update(headers)
        yield client, session_factory
    await engine.dispose()


async def test_identity_me_returns_all_memberships_without_org_selection(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b09_client
    response = await client.get("/api/v1/identity/me", headers={"X-Organization-ID": ""})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["user"]["email"] == "b09@example.test"
    assert {item["organization"]["id"] for item in payload["memberships"]} == {
        _ORG_ID,
        _OTHER_ORG_ID,
    }
    assert response.json()["meta"]["trace_id"] == response.headers["X-Trace-Id"]


async def test_create_organization_assigns_owner_membership(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = b09_client
    response = await client.post(
        "/api/v1/identity/organizations",
        json={"name": "New Organization", "slug": "new-organization"},
    )

    assert response.status_code == 201
    organization_id = response.json()["data"]["id"]
    async with session_factory() as session:
        membership = await session.scalar(
            select(Membership).where(
                Membership.organization_id == organization_id,
                Membership.user_id == "usr_b09_user",
            )
        )
        assert membership is not None
        assert membership.role == "owner"

    duplicate = await client.post(
        "/api/v1/identity/organizations",
        json={"name": "Duplicate", "slug": "new-organization"},
    )
    assert duplicate.status_code == 409


async def test_organization_routes_hide_other_tenants(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b09_client
    response = await client.get(f"/api/v1/identity/organizations/{_OTHER_ORG_ID}")

    assert response.status_code == 404


async def test_organization_update_and_member_listing(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b09_client
    update = await client.patch(
        f"/api/v1/identity/organizations/{_ORG_ID}",
        json={"name": "Renamed", "settings": {"currency": "USD"}},
    )
    members = await client.get(f"/api/v1/identity/organizations/{_ORG_ID}/members")

    assert update.status_code == 200
    assert update.json()["data"]["name"] == "Renamed"
    assert update.json()["data"]["settings"] == {"currency": "USD"}
    assert members.status_code == 200
    assert members.json()["data"][0]["email"] == "b09@example.test"


async def test_catalog_reference_search_paginates_and_brand_list_is_stable(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b09_client
    brands = await client.get("/api/v1/catalog/brands")
    first_page = await client.get("/api/v1/catalog/references?limit=1")

    assert brands.status_code == 200
    assert brands.json()["data"][0]["slug"] == "rolex"
    assert first_page.status_code == 200
    assert len(first_page.json()["data"]) == 1
    meta = first_page.json()["meta"]
    assert meta["has_more"] is True
    second_page = await client.get(
        "/api/v1/catalog/references",
        params={"limit": 1, "cursor": meta["next_cursor"]},
    )
    assert second_page.status_code == 200
    assert second_page.json()["data"][0]["id"] != first_page.json()["data"][0]["id"]


async def test_reference_detail_and_invalid_cursor_are_reported(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b09_client
    page = await client.get("/api/v1/catalog/references?limit=1")
    reference_id = page.json()["data"][0]["id"]

    detail = await client.get(f"/api/v1/catalog/references/{reference_id}")
    invalid_cursor = await client.get(
        "/api/v1/catalog/references",
        params={"cursor": "not-a-valid-cursor"},
    )

    assert detail.status_code == 200
    assert detail.json()["data"]["ref_code"]
    assert invalid_cursor.status_code == 422


async def test_watch_list_crud_is_organization_scoped(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = b09_client
    async with session_factory() as session:
        reference_id = await session.scalar(select(Reference.id).limit(1))
    assert reference_id is not None

    created = await client.post(
        "/api/v1/catalog/watch-lists",
        json={"name": "My watches", "reference_ids": [reference_id]},
    )
    assert created.status_code == 201
    watch_list_id = created.json()["data"]["id"]
    assert len(created.json()["data"]["entries"]) == 1
    invalid = await client.post(
        "/api/v1/catalog/watch-lists",
        json={"name": "Invalid", "reference_ids": ["missing-reference"]},
    )
    assert invalid.status_code == 422

    updated = await client.put(
        f"/api/v1/catalog/watch-lists/{watch_list_id}",
        json={"name": "Updated list", "reference_ids": []},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Updated list"
    assert updated.json()["data"]["entries"] == []

    cross_tenant = await client.put(
        "/api/v1/catalog/watch-lists/wl_b09_other",
        json={"name": "Tampered", "reference_ids": []},
    )
    assert cross_tenant.status_code == 404
    deleted = await client.delete(f"/api/v1/catalog/watch-lists/{watch_list_id}")
    assert deleted.status_code == 204


async def test_catalog_requires_authentication(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b09_client
    response = await client.get(
        "/api/v1/catalog/brands",
        headers={"Authorization": ""},
    )
    channel3_response = await client.post(
        "/api/v1/catalog/channel3/search",
        json={"query": "Rolex"},
        headers={"Authorization": ""},
    )

    assert response.status_code == 401
    assert channel3_response.status_code == 401


async def test_channel3_watch_search_reports_missing_server_key(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    client, _ = b09_client
    monkeypatch.setattr(settings, "channel3_api_key", SecretStr(""))

    with caplog.at_level("WARNING", logger="chronoarb.api"):
        response = await client.post(
            "/api/v1/catalog/channel3/search",
            json={"query": "Rolex Submariner"},
            headers={"X-Trace-Id": "trc_channel3_missing_key"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "not_configured"
    assert response.json()["error"]["message"] == "Search provider is not configured."
    assert response.json()["error"]["retryable"] is False
    assert any(
        record.getMessage() == "channel3_search_failed"
        and record.trace_id == "trc_channel3_missing_key"
        and record.provider_status_code is None
        for record in caplog.records
    )


@pytest.mark.parametrize(
    ("provider_status_code", "code", "message", "retryable", "http_status"),
    [
        (401, "invalid_key", "The search provider key is invalid.", False, 502),
        (402, "credits_exhausted", "Search credits are exhausted.", False, 503),
        (429, "rate_limited", "The search provider is rate limited.", True, 429),
        (
            200,
            "invalid_provider_response",
            "Search provider returned an invalid response.",
            False,
            502,
        ),
    ],
)
async def test_channel3_search_errors_use_specific_safe_envelopes(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    provider_status_code: int,
    code: str,
    message: str,
    retryable: bool,
    http_status: int,
) -> None:
    client, _ = b09_client
    monkeypatch.setattr(settings, "channel3_api_key", SecretStr("test-channel3-key"))

    async def fail_search(
        self: Channel3Client,
        *,
        query: str,
        limit: int,
        page_token: str | None,
    ) -> Channel3SearchResponse:
        raise Channel3UnavailableError(
            provider_status_code,
            code=code,
            message=message,
            retryable=retryable,
        )

    monkeypatch.setattr(Channel3Client, "search", fail_search)
    with caplog.at_level("WARNING", logger="chronoarb.api"):
        response = await client.post(
            "/api/v1/catalog/channel3/search",
            json={"query": "Rolex Submariner"},
            headers={"X-Trace-Id": "trc_channel3_provider_error"},
        )

    assert response.status_code == http_status
    error = response.json()["error"]
    assert error["code"] == code
    assert error["message"].startswith(message)
    assert error["retryable"] is retryable
    assert error["trace_id"] == "trc_channel3_provider_error"
    assert "test-channel3-key" not in response.text
    assert "private-provider-body" not in response.text
    assert any(
        record.getMessage() == "channel3_search_failed"
        and record.trace_id == "trc_channel3_provider_error"
        and record.provider_status_code == provider_status_code
        for record in caplog.records
    )


async def test_channel3_watch_search_returns_authenticated_catalog_results(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = b09_client

    async def fake_search(
        self: Channel3Client,
        *,
        query: str,
        limit: int,
        page_token: str | None,
    ) -> Channel3SearchResponse:
        assert query == "Rolex Submariner"
        assert limit == 5
        assert page_token is None
        return Channel3SearchResponse(
            products=[
                Channel3Product(
                    id="channel3-product-1",
                    title="Submariner",
                    offers=[
                        Channel3Offer(
                            url="https://retailer.example/watch",
                            domain="retailer.example",
                            price=Channel3Price(
                                amount=Decimal("12950.50"),
                                currency="USD",
                            ),
                            availability="InStock",
                            condition="used",
                        )
                    ],
                )
            ],
            next_page_token=None,
            fetched_at=datetime(2026, 11, 11, tzinfo=UTC),
        )

    monkeypatch.setattr(Channel3Client, "search", fake_search)
    response = await client.post(
        "/api/v1/catalog/channel3/search",
        json={"query": "Rolex Submariner", "limit": 5},
    )

    assert response.status_code == 200
    product = response.json()["data"]["products"][0]
    assert product["title"] == "Submariner"
    assert product["offers"][0]["price"] == {
        "amount": "12950.50",
        "currency": "USD",
    }
    assert response.json()["data"]["fetched_at"] == "2026-11-11T00:00:00Z"


async def test_viewer_cannot_mutate_watch_lists(
    b09_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b09_client
    response = await client.post(
        "/api/v1/catalog/watch-lists",
        json={"name": "Viewer list", "reference_ids": []},
        headers={"Authorization": f"Bearer {issue_dev_token('b09-viewer')}"},
    )

    assert response.status_code == 403
