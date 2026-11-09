from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import UTC, datetime

import pytest
from apps.api.identity.api.auth import UnauthorizedError, verify_production_token
from apps.api.identity.infrastructure.models import Membership, Organization, User
from apps.api.infrastructure.database import get_db
from apps.api.infrastructure.models import Base
from apps.api.main import app
from apps.api.settings import settings
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chronoarb.domain.ulid import generate_ulid


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_dev_token(subject: str, secret: str) -> str:
    header = _base64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _base64url(json.dumps({"sub": subject, "exp": int(time.time()) + 300}).encode())
    signing_input = f"{header}.{payload}".encode()
    signature = _base64url(hmac.new(secret.encode(), signing_input, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with sessionmaker() as database_session:
        yield database_session
    await engine.dispose()


@pytest.fixture(autouse=True)
async def configure_identity_auth(monkeypatch):
    monkeypatch.setattr(settings, "auth_mode", "test")
    monkeypatch.setattr(
        settings,
        "dev_jwt_secret",
        "local-test-secret-at-least-32-bytes",
    )


@pytest.fixture
async def client(session):
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_db, None)


def add_user(session: AsyncSession, cognito_sub: str) -> User:
    user = User(
        id=generate_ulid("usr"),
        cognito_sub=cognito_sub,
        email=f"{cognito_sub}@example.com",
        display_name=cognito_sub,
    )
    session.add(user)
    return user


def add_organization(
    session: AsyncSession,
    slug: str,
) -> Organization:
    organization = Organization(
        id=generate_ulid("org"),
        name=f"Organization {slug}",
        slug=slug,
        created_at=datetime.now(UTC),
    )
    session.add(organization)
    return organization


async def test_production_auth_requires_complete_cognito_configuration(monkeypatch):
    monkeypatch.setattr(settings, "auth_mode", "production")
    monkeypatch.setattr(settings, "cognito_jwks_url", "")
    monkeypatch.setattr(settings, "cognito_issuer", "")
    monkeypatch.setattr(settings, "cognito_audience", "")

    with pytest.raises(UnauthorizedError):
        await verify_production_token("not-a-jwt")


class TestIdentityOrganizations:
    async def test_unauthenticated_returns_401(self, client):
        response = await client.get("/api/v1/identity/organizations")

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHORIZED"

    async def test_user_with_no_memberships_returns_empty_list(self, client, session):
        add_user(session, "user-no-orgs")
        await session.commit()

        token = create_dev_token(
            "user-no-orgs",
            settings.dev_jwt_secret,
        )
        response = await client.get(
            "/api/v1/identity/organizations",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_user_with_one_membership_returns_one_org(self, client, session):
        user = add_user(session, "user-one-org")
        organization = add_organization(session, "only-org")
        await session.flush()
        session.add(
            Membership(
                id=generate_ulid("mem"),
                organization_id=organization.id,
                user_id=user.id,
                role="owner",
            )
        )
        await session.commit()

        token = create_dev_token("user-one-org", settings.dev_jwt_secret)
        response = await client.get(
            "/api/v1/identity/organizations",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert [item["slug"] for item in response.json()["data"]] == ["only-org"]

    async def test_user_with_two_orgs_receives_role_for_each(self, client, session):
        user = add_user(session, "user-two-orgs")
        owner_org = add_organization(session, "owner-org")
        dealer_org = add_organization(session, "dealer-org")
        await session.flush()
        session.add_all(
            [
                Membership(
                    id=generate_ulid("mem"),
                    organization_id=owner_org.id,
                    user_id=user.id,
                    role="owner",
                ),
                Membership(
                    id=generate_ulid("mem"),
                    organization_id=dealer_org.id,
                    user_id=user.id,
                    role="dealer",
                ),
            ]
        )
        await session.commit()

        token = create_dev_token("user-two-orgs", settings.dev_jwt_secret)
        response = await client.get(
            "/api/v1/identity/organizations",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert {item["slug"] for item in data} == {"owner-org", "dealer-org"}
        assert {item["role"] for item in data} == {"owner", "dealer"}
        assert response.headers["X-Trace-Id"].startswith("trc_")

    async def test_unknown_subject_returns_401(self, client):
        token = create_dev_token("unknown-user", settings.dev_jwt_secret)

        response = await client.get(
            "/api/v1/identity/organizations",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    async def test_current_user_includes_profile_and_memberships(self, client, session):
        user = add_user(session, "me-user")
        organization = add_organization(session, "me-org")
        await session.flush()
        session.add(
            Membership(
                id=generate_ulid("mem"),
                organization_id=organization.id,
                user_id=user.id,
                role="dealer",
            )
        )
        await session.commit()

        token = create_dev_token("me-user", settings.dev_jwt_secret)
        response = await client.get(
            "/api/v1/identity/me",
            headers={"Authorization": "Bearer " + token},
        )

        assert response.status_code == 200
        assert response.json()["data"]["user"]["email"] == "me-user@example.com"
        assert response.json()["data"]["memberships"][0]["role"] == "dealer"
        assert set(response.json()["meta"]) == {"trace_id", "next_cursor", "has_more"}

    async def test_memberships_are_isolated_by_subject(self, client, session):
        first_user = add_user(session, "first-user")
        second_user = add_user(session, "second-user")
        first_org = add_organization(session, "first-org")
        second_org = add_organization(session, "second-org")
        await session.flush()
        session.add_all(
            [
                Membership(
                    id=generate_ulid("mem"),
                    organization_id=first_org.id,
                    user_id=first_user.id,
                    role="owner",
                ),
                Membership(
                    id=generate_ulid("mem"),
                    organization_id=second_org.id,
                    user_id=second_user.id,
                    role="dealer",
                ),
            ]
        )
        await session.commit()

        token = create_dev_token("first-user", settings.dev_jwt_secret)
        response = await client.get(
            "/api/v1/identity/organizations",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert [item["slug"] for item in response.json()["data"]] == ["first-org"]

    async def test_expired_or_invalid_dev_token_returns_401(self, client):
        response = await client.get(
            "/api/v1/identity/organizations",
            headers={"Authorization": "Bearer not-a-jwt"},
        )

        assert response.status_code == 401
