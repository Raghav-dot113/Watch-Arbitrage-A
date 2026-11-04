from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from collections.abc import AsyncIterator
from typing import Annotated

import pytest
from apps.api.identity.api.auth import (
    AuthContext,
    Permission,
    get_current_auth_context,
    issue_dev_token,
    require_permissions,
)
from apps.api.identity.infrastructure.models import Membership, Organization, User
from apps.api.infrastructure.database import get_db
from apps.api.infrastructure.models import Base
from apps.api.settings import Settings, settings
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_SECRET = "test-only-authentication-secret-32-bytes-minimum"


@pytest.fixture
async def auth_client(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[tuple[AsyncClient, async_sessionmaker[AsyncSession]]]:
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "auth_mode", "dev")
    monkeypatch.setattr(settings, "dev_jwt_secret", SecretStr(_SECRET))
    monkeypatch.setattr(settings, "jwt_issuer", "chronoarb-dev")
    monkeypatch.setattr(settings, "jwt_audience", "chronoarb-api")
    monkeypatch.setattr(settings, "auth_token_ttl_seconds", 900)
    monkeypatch.setattr(settings, "platform_ops_subjects", "ops-sub")

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

    application = FastAPI()
    application.dependency_overrides[get_db] = override_get_db

    @application.get("/tenant")
    async def read_tenant(
        actor: Annotated[AuthContext, Depends(get_current_auth_context)],
    ) -> dict[str, str | None]:
        return {
            "user_id": actor.user_id,
            "organization_id": actor.organization_id,
            "role": actor.role.value,
        }

    @application.get("/billing")
    async def manage_billing(
        actor: Annotated[AuthContext, Depends(require_permissions(Permission.BILLING_MANAGE))],
    ) -> dict[str, str]:
        return {"role": actor.role.value}

    @application.get("/opportunities")
    async def read_opportunities(
        actor: Annotated[AuthContext, Depends(require_permissions(Permission.OPPORTUNITIES_READ))],
    ) -> dict[str, str]:
        return {"role": actor.role.value}

    @application.get("/members")
    async def manage_members(
        actor: Annotated[AuthContext, Depends(require_permissions(Permission.MEMBERS_MANAGE))],
    ) -> dict[str, str]:
        return {"role": actor.role.value}

    @application.get("/alerts")
    async def create_alert(
        actor: Annotated[AuthContext, Depends(require_permissions(Permission.ALERTS_CREATE))],
    ) -> dict[str, str]:
        return {"role": actor.role.value}

    @application.get("/platform")
    async def manage_platform(
        actor: Annotated[AuthContext, Depends(require_permissions(Permission.ADMIN_MANAGE))],
    ) -> dict[str, str | None]:
        return {"organization_id": actor.organization_id, "role": actor.role.value}

    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory
    await engine.dispose()


async def _seed_user(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    subject: str,
    memberships: tuple[tuple[str, str], ...] = (),
) -> None:
    async with session_factory() as session:
        user = User(
            id=f"usr_{subject}",
            cognito_sub=subject,
            email=f"{subject}@example.test",
            display_name=subject,
        )
        session.add(user)
        for organization_id, role in memberships:
            session.add(
                Organization(
                    id=organization_id,
                    name=organization_id,
                    slug=organization_id.replace("_", "-"),
                )
            )
            session.add(
                Membership(
                    id=f"mem_{subject}_{organization_id}",
                    user_id=user.id,
                    organization_id=organization_id,
                    role=role,
                )
            )
        await session.commit()


def _auth_headers(subject: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_dev_token(subject, secret=_SECRET)}"}


def _signed_token(claims: dict[str, object]) -> str:
    header = _encode_segment({"alg": "HS256", "typ": "JWT"})
    payload = _encode_segment(claims)
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = hmac.new(_SECRET.encode(), signing_input, hashlib.sha256).digest()
    return f"{signing_input.decode()}.{_encode_bytes(signature)}"


def _encode_segment(value: dict[str, object]) -> str:
    return _encode_bytes(json.dumps(value, separators=(",", ":")).encode())


def _encode_bytes(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


async def test_authentication_requires_a_valid_bearer_token(auth_client) -> None:
    client, _ = auth_client

    assert (await client.get("/tenant")).status_code == 401
    response = await client.get("/tenant", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_dev_token_expiration_is_enforced(auth_client) -> None:
    client, _ = auth_client
    now = int(time.time())
    token = _signed_token(
        {
            "iss": "chronoarb-dev",
            "aud": "chronoarb-api",
            "sub": "known-sub",
            "iat": now - 60,
            "exp": now - 1,
        },
    )

    response = await client.get("/tenant", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


@pytest.mark.parametrize(
    "claim_overrides",
    [
        {"iss": "unexpected-issuer"},
        {"aud": "unexpected-audience"},
        {"nbf": int(time.time()) + 60},
        {"iat": int(time.time()) + 60},
        {"exp": int(time.time()) + 3600},
    ],
)
async def test_dev_token_validates_issuer_audience_and_time_claims(
    auth_client, claim_overrides: dict[str, object]
) -> None:
    client, _ = auth_client
    now = int(time.time())
    claims: dict[str, object] = {
        "iss": "chronoarb-dev",
        "aud": "chronoarb-api",
        "sub": "known-sub",
        "iat": now,
        "exp": now + 60,
    }
    claims.update(claim_overrides)
    token = _signed_token(claims)

    response = await client.get("/tenant", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


async def test_auth_context_resolves_user_and_membership_from_database(auth_client) -> None:
    client, session_factory = auth_client
    await _seed_user(
        session_factory,
        subject="dealer-sub",
        memberships=(("org_alpha", "dealer"),),
    )

    response = await client.get("/tenant", headers=_auth_headers("dealer-sub"))

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "usr_dealer-sub",
        "organization_id": "org_alpha",
        "role": "dealer",
    }


async def test_user_without_membership_is_denied(auth_client) -> None:
    client, session_factory = auth_client
    await _seed_user(session_factory, subject="unaffiliated-sub")

    response = await client.get("/tenant", headers=_auth_headers("unaffiliated-sub"))

    assert response.status_code == 403


async def test_token_role_claim_cannot_override_database_membership(auth_client) -> None:
    client, session_factory = auth_client
    await _seed_user(
        session_factory,
        subject="viewer-sub",
        memberships=(("org_viewer", "viewer"),),
    )
    now = int(time.time())
    token = _signed_token(
        {
            "iss": "chronoarb-dev",
            "aud": "chronoarb-api",
            "sub": "viewer-sub",
            "role": "owner",
            "iat": now,
            "exp": now + 60,
        }
    )

    response = await client.get("/billing", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


async def test_multiple_memberships_require_a_validated_organization_selection(
    auth_client,
) -> None:
    client, session_factory = auth_client
    await _seed_user(
        session_factory,
        subject="multi-sub",
        memberships=(("org_alpha", "dealer"), ("org_beta", "viewer")),
    )
    headers = _auth_headers("multi-sub")

    assert (await client.get("/tenant", headers=headers)).status_code == 400
    selected = await client.get("/tenant", headers={**headers, "X-Organization-ID": "org_beta"})
    unknown = await client.get("/tenant", headers={**headers, "X-Organization-ID": "org_other"})

    assert selected.status_code == 200
    assert selected.json()["organization_id"] == "org_beta"
    assert selected.json()["role"] == "viewer"
    assert unknown.status_code == 404


async def test_membership_role_controls_permissions(auth_client) -> None:
    client, session_factory = auth_client
    await _seed_user(
        session_factory,
        subject="admin-sub",
        memberships=(("org_admin", "admin"),),
    )
    await _seed_user(
        session_factory,
        subject="dealer-sub",
        memberships=(("org_dealer", "dealer"),),
    )
    await _seed_user(
        session_factory,
        subject="owner-sub",
        memberships=(("org_owner", "owner"),),
    )
    await _seed_user(
        session_factory,
        subject="viewer-sub",
        memberships=(("org_viewer", "viewer"),),
    )

    owner_headers = _auth_headers("owner-sub")
    admin_headers = _auth_headers("admin-sub")
    dealer_headers = _auth_headers("dealer-sub")
    viewer_headers = _auth_headers("viewer-sub")

    assert (await client.get("/billing", headers=owner_headers)).status_code == 200
    assert (await client.get("/members", headers=owner_headers)).status_code == 200
    assert (await client.get("/members", headers=admin_headers)).status_code == 200
    assert (await client.get("/billing", headers=admin_headers)).status_code == 403
    assert (await client.get("/opportunities", headers=viewer_headers)).status_code == 200
    assert (await client.get("/alerts", headers=dealer_headers)).status_code == 200
    assert (await client.get("/billing", headers=dealer_headers)).status_code == 403
    assert (await client.get("/alerts", headers=viewer_headers)).status_code == 403
    assert (await client.get("/billing", headers=viewer_headers)).status_code == 403


async def test_platform_ops_role_requires_server_side_allowlisting(auth_client) -> None:
    client, session_factory = auth_client
    await _seed_user(session_factory, subject="ops-sub")

    response = await client.get("/platform", headers=_auth_headers("ops-sub"))
    assert response.status_code == 200
    assert response.json() == {"organization_id": None, "role": "platform_ops"}

    tenant_selection = await client.get(
        "/platform",
        headers={**_auth_headers("ops-sub"), "X-Organization-ID": "org_alpha"},
    )
    assert tenant_selection.status_code == 400


async def test_unlisted_user_cannot_claim_platform_operator_role(auth_client) -> None:
    client, session_factory = auth_client
    await _seed_user(
        session_factory,
        subject="not-ops",
        memberships=(("org_not_ops", "viewer"),),
    )

    response = await client.get("/platform", headers=_auth_headers("not-ops"))

    assert response.status_code == 403


async def test_oidc_mode_fails_closed_instead_of_accepting_dev_tokens(
    auth_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = auth_client
    headers = _auth_headers("any-sub")
    monkeypatch.setattr(settings, "auth_mode", "oidc")

    response = await client.get("/tenant", headers=headers)

    assert response.status_code == 503


async def test_dev_auth_fails_closed_without_a_configured_secret(
    auth_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = auth_client
    headers = _auth_headers("any-sub")
    monkeypatch.setattr(settings, "dev_jwt_secret", SecretStr(""))

    response = await client.get("/tenant", headers=headers)

    assert response.status_code == 503


def test_settings_reject_development_auth_outside_local_environments() -> None:
    with pytest.raises(ValueError, match="only allowed in local or test"):
        Settings(_env_file=None, environment="production", auth_mode="dev")


def test_token_issuer_requires_a_sufficient_secret() -> None:
    with pytest.raises(ValueError, match="at least 32 bytes"):
        issue_dev_token("user-sub", secret="short")
