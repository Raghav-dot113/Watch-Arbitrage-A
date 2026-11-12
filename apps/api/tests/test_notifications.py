from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from apps.api.alerts.infrastructure.models import AlertDelivery, AlertRule
from apps.api.catalog.infrastructure.models import Brand, Reference, Source
from apps.api.identity.infrastructure.models import Membership, Organization, User
from apps.api.infrastructure.model_registry import get_model_metadata
from apps.api.integrations.application.telegram import (
    TelegramSendResult,
    TelegramService,
    format_opportunity_alert,
)
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.notifications.application.service import NotificationService
from apps.api.operations.infrastructure.models import OutboxEvent
from apps.api.opportunities.infrastructure.models import Opportunity
from apps.api.settings import Settings, settings
from apps.api.valuation.infrastructure.models import Valuation
from pydantic import SecretStr
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_ORG_ID = "org_notify"
_USER_ID = "usr_notify"
_OPPORTUNITY_ID = "opportunity_notify"
_RULE_ID = "rule_notify"


class FakeTelegramSender:
    def __init__(self, result: TelegramSendResult | None = None) -> None:
        self.result = result or TelegramSendResult(
            success=True,
            provider_message_id="telegram-message-42",
        )
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def send_test_alert(
        self,
        chat_id: str,
        *,
        organization_id: str | None = None,
        rule_id: str | None = None,
        trace_id: str | None = None,
    ) -> TelegramSendResult:
        self.calls.append(
            (
                "test",
                chat_id,
                {
                    "organization_id": organization_id,
                    "rule_id": rule_id,
                    "trace_id": trace_id,
                },
            )
        )
        return self.result

    async def send_opportunity_alert(
        self,
        chat_id: str,
        opportunity: dict[str, Any],
        *,
        rule_name: str | None = None,
        base_url: str = "http://localhost:3000",
        trace_id: str | None = None,
    ) -> TelegramSendResult:
        self.calls.append(
            (
                "opportunity",
                chat_id,
                {
                    "opportunity": opportunity,
                    "rule_name": rule_name,
                    "base_url": base_url,
                    "trace_id": trace_id,
                },
            )
        )
        return self.result


@pytest.fixture
async def notification_db(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "auth_mode", "dev")
    monkeypatch.setattr(settings, "telegram_bot_token", SecretStr("test-telegram-token"))
    monkeypatch.setattr(settings, "telegram_chat_id", "chat-from-env")
    monkeypatch.setattr(settings, "web_base_url", "https://app.chronoarb.test")

    engine = create_async_engine("sqlite+aiosqlite://")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(get_model_metadata().create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        session.add_all(
            [
                User(
                    id=_USER_ID,
                    cognito_sub="notify-user",
                    email="notify@example.test",
                    display_name="Notify Tester",
                ),
                Organization(id=_ORG_ID, name="Notify Org", slug="notify-org"),
                Brand(id="brand_notify", name="Rolex", slug="rolex"),
            ]
        )
        await session.flush()
        session.add_all(
            [
                Membership(
                    id="member_notify",
                    organization_id=_ORG_ID,
                    user_id=_USER_ID,
                    role="owner",
                ),
                Reference(
                    id="ref_notify",
                    brand_id="brand_notify",
                    ref_code="126710BLRO",
                    model_name="GMT-Master II",
                    generation="Current",
                ),
                Source(
                    id="source_notify",
                    source_key="notify-fixture",
                    display_name="Notify Fixture",
                    adapter_version="1",
                    access_mode="fixture",
                ),
            ]
        )
        await session.flush()
        session.add(
            RawSnapshot(
                id="snapshot_notify",
                source_id="source_notify",
                external_id="listing-notify",
                adapter_version="1",
                checksum="notify-checksum",
                fetched_at=datetime.now(UTC),
            )
        )
        await session.flush()
        session.add(
            ParsedListing(
                id="parsed_notify",
                snapshot_id="snapshot_notify",
                parser_version="1",
                listing_price=Decimal("14000.00"),
                price_currency="USD",
                listing_title="Rolex GMT-Master II Pepsi",
                description="Full set, excellent condition",
                external_url="https://example.test/notify",
                listed_at=datetime.now(UTC),
                parsed_attributes={"has_box": True, "has_papers": True},
            )
        )
        await session.flush()
        session.add(
            NormalizedListing(
                id="listing_notify",
                parsed_listing_id="parsed_notify",
                reference_id="ref_notify",
                normalization_version="1",
                match_confidence=Decimal("0.9500"),
                match_method="exact_reference",
                match_features={"ref_code": True},
                condition="excellent",
                set_status="full_set",
                seller_geography="US",
                normalized_price=Decimal("14000.00"),
                normalized_currency="USD",
                fx_rate=Decimal("1"),
                fx_source="identity",
                fx_date=date(2026, 11, 1),
                observation_at=datetime.now(UTC) - timedelta(hours=2),
                status="active",
            )
        )
        await session.flush()
        session.add(
            Valuation(
                id="valuation_notify",
                listing_id="listing_notify",
                model_version="valuation-v1",
                config_version="config-v1",
                cost_assumptions_version="ca-2026.1",
                expected_exit_price=Decimal("19000.00"),
                exit_price_currency="USD",
                all_in_acquisition=Decimal("14500.00"),
                expected_net_resale=Decimal("18500.00"),
                expected_net_profit=Decimal("4000.00"),
                roi=Decimal("0.2800"),
                low_estimate=Decimal("17500.00"),
                high_estimate=Decimal("19500.00"),
                confidence=Decimal("0.9000"),
                comparable_count=12,
                sample_dispersion=Decimal("0.1200"),
                cost_breakdown={"fees": "100.00"},
                adjustment_details={"condition": "0.95"},
                risk_reserve_details={"reserve": "50.00"},
            )
        )
        await session.flush()
        session.add(
            Opportunity(
                id=_OPPORTUNITY_ID,
                organization_id=_ORG_ID,
                listing_id="listing_notify",
                valuation_id="valuation_notify",
                material_version=1,
                score=Decimal("0.8500"),
                state="published",
                published_at=datetime.now(UTC),
            )
        )
        session.add(
            AlertRule(
                id=_RULE_ID,
                organization_id=_ORG_ID,
                created_by=_USER_ID,
                name="Telegram deal alerts",
                filters={"min_profit": "1000.00"},
                channels=["telegram"],
                cooldown_minutes=60,
                is_enabled=True,
            )
        )
        await session.commit()

    yield session_factory
    await engine.dispose()


def _add_delivery(session: AsyncSession, **overrides: Any) -> AlertDelivery:
    values: dict[str, Any] = {
        "id": "delivery_notify",
        "organization_id": _ORG_ID,
        "rule_id": _RULE_ID,
        "user_id": _USER_ID,
        "opportunity_id": _OPPORTUNITY_ID,
        "material_version": 1,
        "channel": "telegram",
        "idempotency_key": "notify-delivery-1",
        "delivery_status": "pending",
    }
    values.update(overrides)
    delivery = AlertDelivery(**values)
    session.add(delivery)
    return delivery


def _add_test_event(session: AsyncSession, **overrides: Any) -> OutboxEvent:
    values: dict[str, Any] = {
        "id": "evt_notify_test",
        "event_name": "notification.test_requested",
        "event_version": "1",
        "payload": {
            "channels": ["telegram"],
            "organization_id": _ORG_ID,
            "user_id": _USER_ID,
            "rule_id": _RULE_ID,
            "idempotency_key": "notify-test-1",
            "request_fingerprint": "fingerprint-1",
        },
        "trace_id": "trc_notify_test",
        "status": "pending",
    }
    values.update(overrides)
    outbox_event = OutboxEvent(**values)
    session.add(outbox_event)
    return outbox_event


async def test_dispatch_sends_pending_telegram_delivery_and_records_provider_id(
    notification_db: async_sessionmaker[AsyncSession],
) -> None:
    async with notification_db() as session:
        _add_delivery(session)
        await session.commit()

    sender = FakeTelegramSender()
    async with notification_db() as session:
        summary = await NotificationService(session, telegram=sender).dispatch_once()

    assert summary.deliveries_sent == 1
    assert summary.deliveries_failed == 0
    assert len(sender.calls) == 1
    kind, chat_id, call = sender.calls[0]
    assert kind == "opportunity"
    assert chat_id == "chat-from-env"
    assert call["rule_name"] == "Telegram deal alerts"
    assert call["base_url"] == "https://app.chronoarb.test"
    assert call["opportunity"]["model_name"] == "GMT-Master II"

    async with notification_db() as session:
        delivery = await session.get(AlertDelivery, "delivery_notify")
        assert delivery is not None
        assert delivery.delivery_status == "sent"
        assert delivery.provider_message_id == "telegram-message-42"

    async with notification_db() as session:
        summary = await NotificationService(session, telegram=sender).dispatch_once()

    assert summary.total == 0
    assert len(sender.calls) == 1


async def test_dispatch_suppresses_delivery_without_telegram_destination(
    notification_db: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "telegram_chat_id", "")
    async with notification_db() as session:
        _add_delivery(session)
        await session.commit()

    sender = FakeTelegramSender()
    async with notification_db() as session:
        summary = await NotificationService(session, telegram=sender).dispatch_once()

    assert summary.deliveries_suppressed == 1
    assert sender.calls == []
    async with notification_db() as session:
        delivery = await session.get(AlertDelivery, "delivery_notify")
        assert delivery is not None
        assert delivery.delivery_status == "suppressed"


async def test_dispatch_marks_failed_when_telegram_rejects_message(
    notification_db: async_sessionmaker[AsyncSession],
) -> None:
    async with notification_db() as session:
        _add_delivery(session)
        await session.commit()

    sender = FakeTelegramSender(
        TelegramSendResult(
            success=False,
            error_message="Bad Request: chat not found",
            status_code=400,
        )
    )
    async with notification_db() as session:
        summary = await NotificationService(session, telegram=sender).dispatch_once()

    assert summary.deliveries_failed == 1
    assert len(sender.calls) == 1
    async with notification_db() as session:
        delivery = await session.get(AlertDelivery, "delivery_notify")
        assert delivery is not None
        assert delivery.delivery_status == "failed"
        assert delivery.provider_message_id is None


async def test_dispatch_publishes_queued_telegram_test_notification(
    notification_db: async_sessionmaker[AsyncSession],
) -> None:
    async with notification_db() as session:
        _add_test_event(session)
        await session.commit()

    sender = FakeTelegramSender()
    async with notification_db() as session:
        summary = await NotificationService(session, telegram=sender).dispatch_once()

    assert summary.test_notifications_sent == 1
    assert len(sender.calls) == 1
    kind, chat_id, call = sender.calls[0]
    assert kind == "test"
    assert chat_id == "chat-from-env"
    assert call["rule_id"] == _RULE_ID
    assert call["trace_id"] == "trc_notify_test"

    async with notification_db() as session:
        stored = await session.get(OutboxEvent, "evt_notify_test")
        assert stored is not None
        assert stored.status == "published"
        assert stored.published_at is not None

    async with notification_db() as session:
        summary = await NotificationService(session, telegram=sender).dispatch_once()

    assert summary.total == 0
    assert len(sender.calls) == 1


async def test_dispatch_leaves_non_telegram_test_event_for_other_channel_worker(
    notification_db: async_sessionmaker[AsyncSession],
) -> None:
    async with notification_db() as session:
        _add_test_event(
            session,
            payload={
                "channels": ["push", "in_app"],
                "organization_id": _ORG_ID,
                "user_id": _USER_ID,
                "rule_id": _RULE_ID,
            },
        )
        await session.commit()

    sender = FakeTelegramSender()
    async with notification_db() as session:
        summary = await NotificationService(session, telegram=sender).dispatch_once()

    assert summary.total == 0
    assert sender.calls == []
    async with notification_db() as session:
        stored = await session.get(OutboxEvent, "evt_notify_test")
        assert stored is not None
        assert stored.status == "pending"


async def test_dispatch_fails_test_notification_without_destination(
    notification_db: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "telegram_chat_id", "")
    async with notification_db() as session:
        _add_test_event(session)
        await session.commit()

    sender = FakeTelegramSender()
    async with notification_db() as session:
        summary = await NotificationService(session, telegram=sender).dispatch_once()

    assert summary.test_notifications_failed == 1
    assert sender.calls == []
    async with notification_db() as session:
        stored = await session.get(OutboxEvent, "evt_notify_test")
        assert stored is not None
        assert stored.status == "failed"


async def test_cli_test_message_sends_to_configured_chat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from apps.api.notifications import __main__ as cli

    monkeypatch.setattr(settings, "telegram_chat_id", "-1001234567890")
    monkeypatch.setattr(settings, "telegram_bot_token", SecretStr("token"))
    calls: list[tuple[str, dict[str, Any]]] = []

    async def fake_send_test_alert(
        _service: TelegramService,
        chat_id: str,
        **kwargs: Any,
    ) -> TelegramSendResult:
        calls.append((chat_id, kwargs))
        return TelegramSendResult(success=True, provider_message_id="message-1")

    monkeypatch.setattr(TelegramService, "send_test_alert", fake_send_test_alert)

    exit_code = await cli._send_configured_test_message()

    assert exit_code == 0
    assert calls == [("-1001234567890", {"rule_id": "cli_test"})]


async def test_telegram_service_reports_missing_bot_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "telegram_bot_token", SecretStr(""))

    result = await TelegramService().send_message("chat-id", "hello")

    assert result.success is False
    assert result.error_message is not None
    assert "not configured" in result.error_message


def test_settings_accept_bare_telegram_environment_variable_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CHRONOARB_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("CHRONOARB_TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token-from-env")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001234567890")

    loaded = Settings(_env_file=None)

    assert loaded.telegram_bot_token.get_secret_value() == "bot-token-from-env"
    assert loaded.telegram_chat_id == "-1001234567890"


def test_format_opportunity_alert_includes_required_estimate_metadata() -> None:
    observed_at = datetime.now(UTC) - timedelta(hours=2)
    text = format_opportunity_alert(
        {
            "id": _OPPORTUNITY_ID,
            "brand_name": "Rolex",
            "model_name": "GMT-Master II",
            "ref_code": "126710BLRO",
            "condition": "excellent",
            "set_status": "full_set",
            "source_display_name": "Fixture Source",
            "normalized_price": Decimal("14000.00"),
            "normalized_currency": "USD",
            "expected_exit_price": Decimal("19000.00"),
            "expected_net_resale": Decimal("18500.00"),
            "confidence": Decimal("0.9000"),
            "valuation_version": "valuation-v1",
            "cost_assumptions_version": "ca-2026.1",
            "observation_at": observed_at,
            "material_version": 1,
        },
        base_url="https://app.chronoarb.test",
        rule_name="Telegram deal alerts",
    )

    assert "Rolex — GMT-Master II" in text
    assert "USD 14,000.00" in text
    assert "USD 19,000.00" in text
    assert "Confidence 90%" in text
    assert "Data age 2h" in text
    assert "Valuation valuation-v1" in text
    assert "Costs ca-2026.1" in text
    assert "https://app.chronoarb.test/opportunities/opportunity_notify" in text


def test_format_opportunity_alert_escapes_untrusted_markup() -> None:
    text = format_opportunity_alert(
        {
            "id": "opportunity_escape",
            "brand_name": "<script>alert(1)</script>",
            "model_name": "A & B",
        }
    )

    assert "<script>" not in text
    assert "&lt;script&gt;" in text
    assert "A &amp; B" in text


async def test_notification_dispatch_reads_only_pending_telegram_work(
    notification_db: async_sessionmaker[AsyncSession],
) -> None:
    async with notification_db() as session:
        _add_delivery(session)
        _add_delivery(
            session,
            id="delivery_already_sent",
            idempotency_key="notify-delivery-2",
            delivery_status="sent",
            provider_message_id="telegram-message-1",
        )
        _add_delivery(
            session,
            id="delivery_push",
            idempotency_key="notify-delivery-3",
            channel="push",
        )
        await session.commit()

    sender = FakeTelegramSender()
    async with notification_db() as session:
        summary = await NotificationService(session, telegram=sender).dispatch_once()

    assert summary.deliveries_sent == 1
    assert len(sender.calls) == 1
    async with notification_db() as session:
        statuses = {
            delivery.id: delivery.delivery_status
            for delivery in (
                await session.scalars(select(AlertDelivery).order_by(AlertDelivery.id))
            ).all()
        }
    assert statuses["delivery_already_sent"] == "sent"
    assert statuses["delivery_push"] == "pending"
