from __future__ import annotations

import base64
import json
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal
from urllib.parse import parse_qs, urlsplit

import pytest
from apps.api.billing.application.service import PayPalBillingService
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
    PayPalWebhookEvent,
    ProviderIntegration,
    PushDevice,
)
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.main import create_app
from apps.api.operations.infrastructure.models import FeatureFlag
from apps.api.settings import Settings, settings
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


async def test_b13_paypal_webhook_verification_replay_and_subscription_mapping(
    b13_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, session_factory = b13_client
    monkeypatch.setattr(settings, "paypal_client_id", "client_b13")
    monkeypatch.setattr(settings, "paypal_client_secret", SecretStr("secret_b13"))
    monkeypatch.setattr(settings, "paypal_webhook_id", "webhook_b13")
    async with session_factory() as session:
        session.add(
            Subscription(
                id="sub_b13_paypal",
                organization_id=_ORG_ID,
                paypal_subscription_id="I-B13",
                paypal_approval_url="https://www.sandbox.paypal.com/approve/I-B13",
                status="unpaid",
                plan_id="pro",
            )
        )
        await session.commit()

    event_payload = json.dumps(
        {
            "id": "evt_b13_subscription",
            "event_type": "BILLING.SUBSCRIPTION.ACTIVATED",
            "create_time": "2026-11-07T10:00:00Z",
            "resource": {
                "id": "I-B13",
                "custom_id": _ORG_ID,
                "status": "ACTIVE",
                "subscriber": {"payer_id": "payer_b13"},
                "billing_info": {
                    "last_payment": {"time": "2026-11-01T10:00:00Z"},
                    "next_billing_time": "2026-12-01T10:00:00Z",
                    "cycle_executions": [{"tenure_type": "TRIAL", "cycles_remaining": 1}],
                },
            },
        },
        separators=(",", ":"),
    ).encode()
    webhook_headers = {
        "PayPal-Auth-Algo": "SHA256withRSA",
        "PayPal-Cert-Url": "https://api-m.sandbox.paypal.com/cert",
        "PayPal-Transmission-Id": "transmission_b13",
        "PayPal-Transmission-Sig": "signature_b13",
        "PayPal-Transmission-Time": "2026-11-07T10:00:00Z",
    }
    verification_calls: list[dict[str, object]] = []

    async def mock_paypal_request(
        _service: PayPalBillingService,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
        *,
        request_id: str | None = None,
    ) -> dict[str, str]:
        assert method == "POST"
        assert path == "/v1/notifications/verify-webhook-signature"
        assert request_id is None
        assert payload is not None
        verification_calls.append(payload)
        return {
            "verification_status": (
                "SUCCESS" if payload["transmission_sig"] == "signature_b13" else "FAILURE"
            )
        }

    monkeypatch.setattr(PayPalBillingService, "_paypal_request", mock_paypal_request)
    received = await client.post(
        "/api/v1/billing/webhook",
        content=event_payload,
        headers=webhook_headers,
    )
    replay = await client.post(
        "/api/v1/billing/webhook",
        content=event_payload,
        headers=webhook_headers,
    )
    stale_event = json.loads(event_payload)
    stale_event["id"] = "evt_b13_stale"
    stale_event["event_type"] = "BILLING.SUBSCRIPTION.SUSPENDED"
    stale_event["create_time"] = "2026-11-07T09:00:00Z"
    stale_event["resource"]["status"] = "SUSPENDED"
    stale = await client.post(
        "/api/v1/billing/webhook",
        content=json.dumps(stale_event).encode(),
        headers=webhook_headers,
    )
    invalid = await client.post(
        "/api/v1/billing/webhook",
        content=event_payload,
        headers={**webhook_headers, "PayPal-Transmission-Sig": "invalid"},
    )
    oversized = await client.post(
        "/api/v1/billing/webhook",
        content=b"x" * 1_000_001,
        headers=webhook_headers,
    )
    subscription = await client.get("/api/v1/billing/subscription")

    assert received.status_code == 200, received.text
    assert received.json()["duplicate"] is False
    assert replay.status_code == 200
    assert replay.json()["duplicate"] is True
    assert stale.status_code == 200
    assert stale.json()["duplicate"] is False
    assert invalid.status_code == 400
    assert oversized.status_code == 413
    assert subscription.status_code == 200
    assert subscription.json()["data"]["status"] == "trialing"
    assert subscription.json()["data"]["plan_id"] == "pro"
    assert verification_calls[0]["webhook_id"] == "webhook_b13"
    assert verification_calls[0]["webhook_event"]["id"] == "evt_b13_subscription"

    async with session_factory() as session:
        webhook_event = await session.get(PayPalWebhookEvent, "evt_b13_subscription")
        stored = await session.get(Subscription, "sub_b13_paypal")
        assert webhook_event is not None
        assert stored is not None
        assert await session.get(PayPalWebhookEvent, "evt_b13_stale") is not None
        assert stored.status == "trialing"
        assert stored.paypal_payer_id == "payer_b13"
        assert stored.current_period_end is not None
        assert stored.current_period_end.replace(tzinfo=UTC) == datetime(
            2026, 12, 1, 10, tzinfo=UTC
        )


def test_paypal_api_url_rejects_non_paypal_hosts() -> None:
    with pytest.raises(ValueError, match="official PayPal API host"):
        Settings(paypal_api_base_url="https://paypal.example.invalid")


async def test_b13_paypal_checkout_is_configured_idempotent_and_cancelable(
    b13_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, session_factory = b13_client
    monkeypatch.setattr(settings, "paypal_plan_ids", {"pro": "P-PRO-B13"})
    monkeypatch.setattr(settings, "paypal_client_id", "")
    monkeypatch.setattr(settings, "paypal_client_secret", SecretStr(""))

    checkout_headers = {"Idempotency-Key": "checkout-b13-1"}
    checkout = await client.post(
        "/api/v1/billing/checkout",
        json={"plan_id": "pro"},
        headers=checkout_headers,
    )
    unconfigured_plan = await client.post(
        "/api/v1/billing/checkout",
        json={"plan_id": "missing"},
        headers=checkout_headers,
    )
    missing_key = await client.post(
        "/api/v1/billing/checkout",
        json={"plan_id": "pro"},
    )
    unconfigured_cancel = await client.post(
        "/api/v1/billing/cancel",
        headers={"Idempotency-Key": "cancel-b13-1"},
    )

    assert checkout.status_code == 503
    assert unconfigured_plan.status_code == 422
    assert missing_key.status_code == 422
    assert unconfigured_cancel.status_code == 503

    monkeypatch.setattr(settings, "paypal_client_id", "client_b13")
    monkeypatch.setattr(settings, "paypal_client_secret", SecretStr("secret_b13"))
    calls: list[tuple[str, str, dict[str, object] | None, str | None]] = []
    approval_url = "https://www.sandbox.paypal.com/approve/I-CREATED-B13"

    async def mock_paypal_request(
        _service: PayPalBillingService,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
        *,
        request_id: str | None = None,
    ) -> dict[str, str]:
        calls.append((method, path, payload, request_id))
        if path == "/v1/billing/subscriptions":
            return {
                "id": "I-CREATED-B13",
                "links": [{"rel": "approve", "href": approval_url}],
            }
        return {}

    monkeypatch.setattr(PayPalBillingService, "_paypal_request", mock_paypal_request)
    created = await client.post(
        "/api/v1/billing/checkout",
        json={"plan_id": "pro"},
        headers=checkout_headers,
    )
    resumed = await client.post(
        "/api/v1/billing/checkout",
        json={"plan_id": "pro"},
        headers=checkout_headers,
    )
    canceled = await client.post(
        "/api/v1/billing/cancel",
        headers={"Idempotency-Key": "cancel-b13-1"},
    )

    assert created.status_code == 200, created.text
    assert created.json()["data"] == {
        "subscription_id": "I-CREATED-B13",
        "url": approval_url,
    }
    assert resumed.status_code == 200
    assert resumed.json()["data"] == created.json()["data"]
    assert canceled.status_code == 200
    assert canceled.json()["data"]["status"] == "canceled"
    assert calls[0][0:2] == ("POST", "/v1/billing/subscriptions")
    assert calls[0][2]["plan_id"] == "P-PRO-B13"
    assert calls[0][2]["custom_id"] == _ORG_ID
    assert calls[0][3] is not None and len(calls[0][3]) == 36
    assert calls[1][0:2] == (
        "POST",
        "/v1/billing/subscriptions/I-CREATED-B13/cancel",
    )
    assert calls[1][3] is not None and len(calls[1][3]) == 36

    async with session_factory() as session:
        subscription = (
            await session.scalars(
                select(Subscription).where(Subscription.organization_id == _ORG_ID)
            )
        ).one()
        assert subscription.status == "canceled"


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
