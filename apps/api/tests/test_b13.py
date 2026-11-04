from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest
from apps.api.billing.application.service import StripeBillingService
from apps.api.billing.infrastructure.models import Subscription
from apps.api.catalog.infrastructure.models import Brand, Reference, Source
from apps.api.duplicates.infrastructure.models import DuplicateGroup, DuplicateGroupMember
from apps.api.identity.api.auth import issue_dev_token
from apps.api.identity.infrastructure.models import Membership, Organization, User
from apps.api.infrastructure.database import get_db
from apps.api.infrastructure.models import Base
from apps.api.integrations.application.crypto import decrypt_provider_secret, digest_token
from apps.api.integrations.application.service import IntegrationService
from apps.api.integrations.infrastructure.models import (
    ProviderIntegration,
    PushDevice,
    StripeWebhookEvent,
)
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.main import create_app
from apps.api.operations.infrastructure.models import FeatureFlag
from apps.api.settings import settings
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_SECRET = "b13-test-only-authentication-secret-32-bytes"
_ORG_ID = "org_b13"
_OTHER_ORG_ID = "org_b13_other"
_TOKEN_KEY = base64.urlsafe_b64encode(b"b13-encryption-key-is-32-bytes!!").decode("ascii")


@pytest.fixture
async def b13_client(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[tuple[AsyncClient, async_sessionmaker[AsyncSession]]]:
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "auth_mode", "dev")
    monkeypatch.setattr(settings, "dev_jwt_secret", SecretStr(_SECRET))
    monkeypatch.setattr(settings, "jwt_issuer", "chronoarb-dev")
    monkeypatch.setattr(settings, "jwt_audience", "chronoarb-api")
    monkeypatch.setattr(settings, "platform_ops_subjects", "b13-ops")
    monkeypatch.setattr(settings, "integration_encryption_key", SecretStr(_TOKEN_KEY))
    monkeypatch.setattr(settings, "telegram_bot_token", SecretStr("test-telegram-bot-token"))
    monkeypatch.setattr(settings, "telegram_bot_username", "chronoarb_test_bot")

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
        owner = User(
            id="usr_b13_owner",
            cognito_sub="b13-owner",
            email="owner@example.test",
        )
        viewer = User(
            id="usr_b13_viewer",
            cognito_sub="b13-viewer",
            email="viewer@example.test",
        )
        operator = User(
            id="usr_b13_ops",
            cognito_sub="b13-ops",
            email="ops@example.test",
        )
        org = Organization(
            id=_ORG_ID,
            name="B13 Org",
            slug="b13-org",
            settings={"existing_setting": "preserve"},
        )
        other_org = Organization(
            id=_OTHER_ORG_ID,
            name="Other Org",
            slug="b13-other",
        )
        brand = Brand(id="brand_b13", name="B13 Brand", slug="b13-brand")
        reference = Reference(
            id="ref_b13",
            brand_id=brand.id,
            ref_code="B13-1",
            model_name="B13 Watch",
        )
        source = Source(
            id="source_b13",
            source_key="b13-fixture",
            display_name="B13 Fixture",
            adapter_version="1",
            access_mode="fixture",
        )
        session.add_all([owner, viewer, operator, org, other_org, brand, reference, source])
        await session.flush()
        session.add_all(
            [
                Membership(
                    id="member_b13_owner",
                    organization_id=org.id,
                    user_id=owner.id,
                    role="owner",
                ),
                Membership(
                    id="member_b13_viewer",
                    organization_id=org.id,
                    user_id=viewer.id,
                    role="viewer",
                ),
                RawSnapshot(
                    id="snapshot_b13",
                    source_id=source.id,
                    external_id="listing-b13",
                    adapter_version="1",
                    checksum="b13-checksum",
                    fetched_at=datetime(2026, 11, 4, tzinfo=UTC),
                ),
            ]
        )
        await session.flush()
        session.add(
            ParsedListing(
                id="parsed_b13",
                snapshot_id="snapshot_b13",
                parser_version="1",
                listing_title="Unmatched watch",
                external_url="https://example.test/b13",
            )
        )
        await session.flush()
        session.add(
            NormalizedListing(
                id="listing_b13",
                parsed_listing_id="parsed_b13",
                reference_id=reference.id,
                normalization_version="1",
                match_confidence=None,
                fx_rate=Decimal("1"),
                fx_source="identity",
                fx_date=date(2026, 11, 4),
                observation_at=datetime(2026, 11, 4, tzinfo=UTC),
                status="active",
            )
        )
        await session.flush()
        session.add_all(
            [
                FeatureFlag(
                    id="flag_b13",
                    key="b13-feature",
                    description="B13 test flag",
                    enabled=False,
                    rollout_pct=0,
                ),
                DuplicateGroup(
                    id="duplicates_b13",
                    representative_id="listing_b13",
                    model_version="v1",
                    method="fixture",
                    confidence=Decimal("0.9000"),
                ),
                DuplicateGroupMember(
                    id="duplicate_member_b13",
                    group_id="duplicates_b13",
                    listing_id="listing_b13",
                ),
            ]
        )
        await session.commit()

    owner_headers = {
        "Authorization": f"Bearer {issue_dev_token('b13-owner')}",
        "X-Organization-ID": _ORG_ID,
    }
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.headers.update(owner_headers)
        yield client, session_factory
    await engine.dispose()


async def test_b13_organization_settings_merge_validate_and_enforce_roles(
    b13_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = b13_client
    initial = await client.get("/api/v1/settings/organization")
    updated = await client.patch(
        "/api/v1/settings/organization",
        json={
            "currency": "EUR",
            "timezone": "Europe/Paris",
            "default_fees": {"buyer_fee": "12.50", "selling_fee": "25.00"},
        },
    )
    invalid_money = await client.patch(
        "/api/v1/settings/organization",
        json={"default_fees": {"buyer_fee": 12.5}},
    )
    null_currency = await client.patch(
        "/api/v1/settings/organization",
        json={"currency": None},
    )
    viewer_headers = {
        "Authorization": f"Bearer {issue_dev_token('b13-viewer')}",
        "X-Organization-ID": _ORG_ID,
    }
    forbidden = await client.patch(
        "/api/v1/settings/organization",
        json={"currency": "USD"},
        headers=viewer_headers,
    )

    assert initial.status_code == 200
    assert initial.json()["data"]["currency"] == "USD"
    assert initial.json()["data"]["timezone"] == "UTC"
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["currency"] == "EUR"
    assert updated.json()["data"]["default_fees"]["buyer_fee"] == "12.50"
    assert invalid_money.status_code == 422
    assert null_currency.status_code == 422
    assert forbidden.status_code == 403

    async with session_factory() as session:
        organization = await session.get(Organization, _ORG_ID)
        assert organization is not None
        assert organization.settings == {
            "existing_setting": "preserve",
            "currency": "EUR",
            "timezone": "Europe/Paris",
            "default_fees": {"buyer_fee": "12.50", "selling_fee": "25.00"},
        }


async def test_b13_integrations_encrypt_tokens_and_scope_unlinking(
    b13_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = b13_client
    device_token = "fcm_device_token_b13_test_value_123456789"
    registered = await client.post(
        "/api/v1/settings/integrations/push",
        json={"platform": "ios", "device_token": device_token},
    )
    assert registered.status_code == 201, registered.text
    device_id = registered.json()["data"]["id"]
    assert device_token not in registered.text

    async with session_factory() as session:
        device = await session.get(PushDevice, device_id)
        assert device is not None
        assert device.token_hash == digest_token(device_token)
        assert device.token_ciphertext != device_token
        assert decrypt_provider_secret(device.token_ciphertext) == device_token

    viewer_headers = {
        "Authorization": f"Bearer {issue_dev_token('b13-viewer')}",
        "X-Organization-ID": _ORG_ID,
    }
    token_conflict = await client.post(
        "/api/v1/settings/integrations/push",
        json={"platform": "android", "device_token": device_token},
        headers=viewer_headers,
    )
    foreign_delete = await client.delete(
        f"/api/v1/settings/integrations/push/{device_id}",
        headers=viewer_headers,
    )
    unregistered = await client.delete(
        f"/api/v1/settings/integrations/push/{device_id}",
    )

    assert token_conflict.status_code == 409
    assert foreign_delete.status_code == 404
    assert unregistered.status_code == 204

    link = await client.post("/api/v1/settings/integrations/telegram")
    assert link.status_code == 201, link.text
    token = parse_qs(urlsplit(link.json()["data"]["link_url"]).query)["start"][0]
    async with session_factory() as session:
        integration = (
            await session.scalars(
                select(ProviderIntegration).where(
                    ProviderIntegration.organization_id == _ORG_ID,
                    ProviderIntegration.provider == "telegram",
                )
            )
        ).one()
        assert integration.status == "pending"
        assert integration.link_token_hash == digest_token(token)
        assert integration.link_token_hash != token
        await IntegrationService(session).complete_telegram_link(token, "telegram-chat-b13")
        assert integration.status == "connected"
        assert integration.external_id_ciphertext is not None
        assert decrypt_provider_secret(integration.external_id_ciphertext) == "telegram-chat-b13"

    status_response = await client.get("/api/v1/settings/integrations")
    disconnected = await client.delete("/api/v1/settings/integrations/telegram")
    assert status_response.status_code == 200
    assert status_response.json()["data"]["telegram_status"] == "connected"
    assert disconnected.status_code == 204


async def test_b13_stripe_webhook_signature_replay_and_subscription_mapping(
    b13_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, session_factory = b13_client
    monkeypatch.setattr(settings, "stripe_webhook_secret", SecretStr("whsec_b13"))
    event_payload = json.dumps(
        {
            "id": "evt_b13_subscription",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_b13",
                    "customer": "cus_b13",
                    "status": "active",
                    "metadata": {"organization_id": _ORG_ID, "plan_id": "pro"},
                    "current_period_start": 1793750400,
                    "current_period_end": 1796342400,
                    "trial_end": None,
                }
            },
        },
        separators=(",", ":"),
    ).encode()
    timestamp = int(time.time())
    signed = str(timestamp).encode() + b"." + event_payload
    signature = hmac.new(b"whsec_b13", signed, hashlib.sha256).hexdigest()
    headers = {"Stripe-Signature": f"t={timestamp},v1={signature}"}
    received = await client.post("/api/v1/billing/webhook", content=event_payload, headers=headers)
    replay = await client.post("/api/v1/billing/webhook", content=event_payload, headers=headers)
    invalid = await client.post(
        "/api/v1/billing/webhook",
        content=event_payload,
        headers={"Stripe-Signature": f"t={timestamp},v1={'0' * 64}"},
    )
    oversized = await client.post(
        "/api/v1/billing/webhook",
        content=b"x" * 1_000_001,
        headers=headers,
    )
    subscription = await client.get("/api/v1/billing/subscription")

    assert received.status_code == 200, received.text
    assert received.json()["duplicate"] is False
    assert replay.status_code == 200
    assert replay.json()["duplicate"] is True
    assert invalid.status_code == 400
    assert oversized.status_code == 413
    assert subscription.status_code == 200
    assert subscription.json()["data"]["status"] == "active"
    assert subscription.json()["data"]["plan_id"] == "pro"

    async with session_factory() as session:
        webhook_event = await session.get(StripeWebhookEvent, "evt_b13_subscription")
        stored = await session.scalars(
            select(Subscription).where(Subscription.organization_id == _ORG_ID)
        )
        assert webhook_event is not None
        assert len(list(stored.all())) == 1


async def test_b13_billing_provider_configuration_fails_explicitly(
    b13_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, session_factory = b13_client
    monkeypatch.setattr(settings, "stripe_price_ids", {"pro": "price_b13"})
    monkeypatch.setattr(settings, "stripe_secret_key", SecretStr(""))

    checkout = await client.post("/api/v1/billing/checkout", json={"plan_id": "pro"})
    unconfigured_plan = await client.post("/api/v1/billing/checkout", json={"plan_id": "missing"})
    portal = await client.post("/api/v1/billing/portal")

    assert checkout.status_code == 503
    assert unconfigured_plan.status_code == 422
    assert portal.status_code == 503

    calls: list[tuple[str, dict[str, str]]] = []

    async def mock_stripe_post(
        _service: StripeBillingService,
        path: str,
        form_data: dict[str, str],
    ) -> dict[str, str]:
        calls.append((path, form_data))
        if path == "/v1/checkout/sessions":
            return {"id": "cs_b13", "url": "https://checkout.stripe.com/cs_b13"}
        return {"url": "https://billing.stripe.com/session_b13"}

    monkeypatch.setattr(StripeBillingService, "_stripe_post", mock_stripe_post)
    monkeypatch.setattr(settings, "stripe_secret_key", SecretStr("sk_test_b13"))
    async with session_factory() as session:
        session.add(
            Subscription(
                id="sub_b13_existing",
                organization_id=_ORG_ID,
                stripe_customer_id="cus_b13",
                status="active",
                plan_id="pro",
            )
        )
        await session.commit()

    configured_checkout = await client.post("/api/v1/billing/checkout", json={"plan_id": "pro"})
    configured_portal = await client.post("/api/v1/billing/portal")

    assert configured_checkout.status_code == 200, configured_checkout.text
    assert configured_checkout.json()["data"]["session_id"] == "cs_b13"
    assert configured_checkout.json()["data"]["url"] == "https://checkout.stripe.com/cs_b13"
    assert configured_portal.status_code == 200, configured_portal.text
    assert configured_portal.json()["data"]["url"] == "https://billing.stripe.com/session_b13"
    assert calls[0][0] == "/v1/checkout/sessions"
    assert calls[0][1]["line_items[0][price]"] == "price_b13"
    assert calls[0][1]["metadata[organization_id]"] == _ORG_ID
    assert calls[1] == (
        "/v1/billing_portal/sessions",
        {"customer": "cus_b13", "return_url": settings.stripe_portal_return_url},
    )


async def test_b13_platform_admin_routes_audit_and_queue_operations(
    b13_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = b13_client
    client.headers.pop("X-Organization-ID")
    operator_headers = {"Authorization": f"Bearer {issue_dev_token('b13-ops')}"}
    forbidden = await client.get("/api/v1/admin/sources")
    sources = await client.get("/api/v1/admin/sources", headers=operator_headers)
    disabled = await client.patch(
        "/api/v1/admin/sources/source_b13",
        json={"is_enabled": False},
        headers=operator_headers,
    )
    flags = await client.get("/api/v1/admin/flags", headers=operator_headers)
    updated_flag = await client.patch(
        "/api/v1/admin/flags/flag_b13",
        json={"enabled": True, "rollout_pct": 35},
        headers=operator_headers,
    )
    unmatched = await client.get("/api/v1/admin/unmatched", headers=operator_headers)
    resolved = await client.post(
        "/api/v1/admin/unmatched/listing_b13/resolve",
        json={"reference_id": "ref_b13"},
        headers=operator_headers,
    )
    duplicate_groups = await client.get("/api/v1/admin/duplicates", headers=operator_headers)
    audit = await client.get("/api/v1/admin/audit", headers=operator_headers)
    jobs = await client.get("/api/v1/admin/jobs", headers=operator_headers)
    dlq = await client.delete(
        "/api/v1/admin/dlq/message_b13",
        headers=operator_headers,
    )

    assert forbidden.status_code == 403
    assert sources.status_code == 200, sources.text
    source = sources.json()["data"][0]
    assert source["health_status"] == "unknown"
    assert source["last_fetched_at"] is not None
    assert disabled.status_code == 200
    assert disabled.json()["data"]["is_enabled"] is False
    assert flags.status_code == 200
    assert updated_flag.status_code == 200
    assert updated_flag.json()["data"]["rollout_pct"] == 35
    assert unmatched.status_code == 200
    assert [item["id"] for item in unmatched.json()["data"]] == ["listing_b13"]
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["data"]["source_key"] == "b13-fixture"
    assert resolved.json()["data"]["match_method"] == "manual_review"
    assert duplicate_groups.status_code == 200
    assert duplicate_groups.json()["data"][0]["listing_ids"] == ["listing_b13"]
    assert audit.status_code == 200
    assert jobs.status_code == 503
    assert dlq.status_code == 503

    async with session_factory() as session:
        listing = await session.get(NormalizedListing, "listing_b13")
        assert listing is not None
        assert listing.match_confidence == Decimal("1.0000")
        assert listing.match_method == "manual_review"
        assert await session.get(FeatureFlag, "flag_b13") is not None
