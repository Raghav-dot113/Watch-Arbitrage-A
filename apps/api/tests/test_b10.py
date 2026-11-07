from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from apps.api.alerts.infrastructure.models import AlertDelivery, AlertRule
from apps.api.catalog.infrastructure.models import Brand, Reference, Source
from apps.api.feedback.infrastructure.models import Feedback, TradeOutcome
from apps.api.identity.api.auth import issue_dev_token
from apps.api.identity.infrastructure.models import Membership, Organization, User
from apps.api.infrastructure.database import get_db
from apps.api.infrastructure.models import Base
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.main import create_app
from apps.api.operations.infrastructure.models import AuditEvent, OutboxEvent
from apps.api.opportunities.infrastructure.models import Opportunity
from apps.api.settings import settings
from apps.api.valuation.infrastructure.models import Valuation
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_SECRET = "b10-test-only-authentication-secret-32-bytes"
_SUBJECT = "b10-user"
_ORG_ID = "org_b10_primary"
_OTHER_ORG_ID = "org_b10_other"


@pytest.fixture
async def b10_client(
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
            id="usr_b10_user",
            cognito_sub=_SUBJECT,
            email="b10@example.test",
            display_name="B10 Tester",
        )
        viewer = User(
            id="usr_b10_viewer",
            cognito_sub="b10-viewer",
            email="viewer@example.test",
            display_name="B10 Viewer",
        )
        org = Organization(id=_ORG_ID, name="Primary", slug="b10-primary")
        other_org = Organization(id=_OTHER_ORG_ID, name="Other", slug="b10-other")
        brand = Brand(id="brand_b10", name="Example", slug="example")
        reference = Reference(
            id="ref_b10",
            brand_id=brand.id,
            ref_code="EX-1",
            model_name="Example Watch",
            generation="Gen 1",
            attributes={"material": "steel"},
        )
        source = Source(
            id="source_b10",
            source_key="fixture",
            display_name="Fixture Source",
            adapter_version="1",
            access_mode="fixture",
        )
        session.add_all([user, viewer, org, other_org, brand, reference, source])
        await session.flush()
        session.add_all(
            [
                Membership(
                    id="mem_b10",
                    organization_id=org.id,
                    user_id=user.id,
                    role="owner",
                ),
                Membership(
                    id="mem_b10_viewer",
                    organization_id=org.id,
                    user_id=viewer.id,
                    role="viewer",
                ),
            ]
        )
        await session.flush()
        for suffix, profit in (("one", Decimal("500.00")), ("two", Decimal("300.00"))):
            snapshot = RawSnapshot(
                id=f"raw_b10_{suffix}",
                source_id=source.id,
                external_id=f"ext_b10_{suffix}",
                adapter_version="1",
                checksum=f"checksum_b10_{suffix}",
            )
            session.add(snapshot)
            await session.flush()
            parsed = ParsedListing(
                id=f"parsed_b10_{suffix}",
                snapshot_id=snapshot.id,
                parser_version="1",
                listing_price=Decimal("1000.00"),
                price_currency="USD",
                listing_title=f"Listing {suffix}",
                description="Verified listing description",
                external_url=f"https://example.test/{suffix}",
                listed_at=datetime(2026, 1, 1, tzinfo=UTC),
                parsed_attributes={"dial": "blue"},
            )
            session.add(parsed)
            await session.flush()
            listing = NormalizedListing(
                id=f"listing_b10_{suffix}",
                parsed_listing_id=parsed.id,
                reference_id=reference.id,
                normalization_version="1",
                match_confidence=Decimal("0.9500"),
                match_method="exact_reference",
                match_features={"ref_code": True},
                condition="excellent",
                set_status="full_set",
                seller_geography="US",
                normalized_price=Decimal("1000.00"),
                normalized_currency="USD",
                fx_rate=Decimal("1"),
                fx_source="identity",
                fx_date=date(2026, 1, 1),
                observation_at=datetime(2026, 1, 1, tzinfo=UTC),
                status="active",
            )
            session.add(listing)
            await session.flush()
            valuation = Valuation(
                id=f"valuation_b10_{suffix}",
                listing_id=listing.id,
                model_version="valuation-v1",
                config_version="config-v1",
                cost_assumptions_version="ca-2026.1",
                expected_exit_price=Decimal("1700.00"),
                exit_price_currency="USD",
                all_in_acquisition=Decimal("1100.00"),
                expected_net_resale=Decimal("1600.00"),
                expected_net_profit=profit,
                roi=profit / Decimal("1100.00"),
                low_estimate=Decimal("1500.00"),
                high_estimate=Decimal("1800.00"),
                confidence=Decimal("0.9000"),
                comparable_count=12,
                sample_dispersion=Decimal("0.1200"),
                cost_breakdown={"fees": "100.00"},
                adjustment_details={"condition": "0.95"},
                risk_reserve_details={"reserve": "50.00"},
            )
            session.add(valuation)
            await session.flush()
            session.add(
                Opportunity(
                    id=f"opportunity_b10_{suffix}",
                    organization_id=org.id,
                    listing_id=listing.id,
                    valuation_id=valuation.id,
                    material_version=1,
                    score=Decimal("0.7500"),
                    state="published",
                    positive_factors=["price"],
                    negative_factors=[],
                    published_at=datetime(2026, 1, 1, tzinfo=UTC),
                )
            )
            if suffix == "one":
                other_tenant_opportunity = Opportunity(
                    id="opportunity_b10_other",
                    organization_id=other_org.id,
                    listing_id=listing.id,
                    valuation_id=valuation.id,
                    material_version=1,
                    score=Decimal("0.7500"),
                    state="published",
                )
                session.add(other_tenant_opportunity)
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


async def test_opportunity_feed_filters_paginates_and_includes_freshness(
    b10_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b10_client
    first_page = await client.get(
        "/api/v1/opportunities",
        params={"limit": 1, "sort": "profit_desc"},
    )

    assert first_page.status_code == 200
    payload = first_page.json()
    assert len(payload["data"]) == 1
    first = payload["data"][0]
    assert first["id"] == "opportunity_b10_one"
    assert first["confidence"] == "0.9000"
    assert first["valuation_version"] == "valuation-v1"
    assert first["cost_assumptions_version"] == "ca-2026.1"
    assert first["data_age_seconds"] >= 0
    assert payload["meta"]["has_more"] is True
    assert payload["meta"]["next_cursor"]

    second_page = await client.get(
        "/api/v1/opportunities",
        params={
            "limit": 1,
            "sort": "profit_desc",
            "cursor": payload["meta"]["next_cursor"],
        },
    )
    filtered = await client.get(
        "/api/v1/opportunities",
        params={"min_profit": "400.00"},
    )
    assert second_page.status_code == 200
    assert second_page.json()["data"][0]["id"] == "opportunity_b10_two"
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["data"]] == ["opportunity_b10_one"]


async def test_opportunity_detail_contains_lineage_and_hides_other_tenants(
    b10_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b10_client
    detail = await client.get("/api/v1/opportunities/opportunity_b10_one")
    other_tenant = await client.get("/api/v1/opportunities/opportunity_b10_other")

    assert detail.status_code == 200
    body = detail.json()["data"]
    assert body["observation_at"] == "2026-01-01T00:00:00Z"
    assert body["data_age_seconds"] >= 0
    assert body["state_changed_at"] is None
    assert body["listing"]["external_url"] == "https://example.test/one"
    assert body["listing"]["reference_attributes"] == {"material": "steel"}
    assert body["valuation"]["expected_net_profit"] == "500.00"
    assert body["valuation"]["comparable_count"] == 12
    assert body["valuation"]["cost_breakdown"] == {"fees": "100.00"}
    assert body["valuation"]["adjustment_details"] == {"condition": "0.95"}
    assert other_tenant.status_code == 404


async def test_opportunity_routes_reject_invalid_queries_and_missing_auth(
    b10_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b10_client
    invalid_cursor = await client.get(
        "/api/v1/opportunities",
        params={"cursor": "not-a-valid-cursor"},
    )
    unauthorized = await client.get(
        "/api/v1/opportunities",
        headers={"Authorization": ""},
    )

    assert invalid_cursor.status_code == 422
    assert unauthorized.status_code == 401


async def test_b11_feedback_is_atomic_idempotent_and_transitions_once(
    b10_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = b10_client
    path = "/api/v1/opportunities/opportunity_b10_one/feedback"
    headers = {"Idempotency-Key": "b11-feedback-001"}
    request = {"decision": "contacted", "notes": "Seller contacted"}

    created = await client.post(path, json=request, headers=headers)
    replay = await client.post(path, json=request, headers=headers)
    key_conflict = await client.post(
        path,
        json={"decision": "dismissed", "notes": "different request"},
        headers=headers,
    )
    invalid_transition = await client.post(
        path,
        json={"decision": "purchased"},
        headers={"Idempotency-Key": "b11-feedback-002"},
    )
    contact_feed = await client.get(
        "/api/v1/opportunities",
        params={"state": "contacted"},
    )

    assert created.status_code == 201, created.text
    assert created.json()["data"]["opportunity_state"] == "contacted"
    assert replay.status_code == 200
    assert replay.json()["data"]["feedback"]["id"] == created.json()["data"]["feedback"]["id"]
    assert key_conflict.status_code == 409
    assert invalid_transition.status_code == 409
    assert contact_feed.status_code == 200
    assert contact_feed.json()["data"][0]["my_decision"] == "contacted"

    async with session_factory() as session:
        audit_events = list(
            (
                await session.scalars(
                    select(AuditEvent).where(AuditEvent.action == "opportunity.feedback_recorded")
                )
            ).all()
        )
        assert len(audit_events) == 1


async def test_b11_history_returns_tenant_scoped_material_versions(
    b10_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = b10_client
    async with session_factory() as session:
        session.add(
            Opportunity(
                id="opportunity_b10_one_v2",
                organization_id=_ORG_ID,
                listing_id="listing_b10_one",
                valuation_id="valuation_b10_one",
                material_version=2,
                score=Decimal("0.8000"),
                state="published",
                published_at=datetime(2026, 2, 1, tzinfo=UTC),
            )
        )
        await session.commit()

    history = await client.get("/api/v1/opportunities/opportunity_b10_one_v2/history")
    old_version = await client.get("/api/v1/opportunities/opportunity_b10_one/history")
    other_tenant = await client.get("/api/v1/opportunities/opportunity_b10_other/history")

    assert history.status_code == 200
    versions = history.json()["data"]
    assert [version["material_version"] for version in versions] == [2, 1]
    assert versions[0]["valuation"]["expected_net_profit"] == "500.00"
    assert old_version.status_code == 200
    assert [version["material_version"] for version in old_version.json()["data"]] == [2, 1]
    assert other_tenant.status_code == 404


async def test_b11_viewer_can_read_history_but_cannot_write_decisions(
    b10_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = b10_client
    viewer_headers = {
        "Authorization": f"Bearer {issue_dev_token('b10-viewer')}",
        "X-Organization-ID": _ORG_ID,
    }

    history = await client.get(
        "/api/v1/opportunities/opportunity_b10_one/history",
        headers=viewer_headers,
    )
    feedback = await client.post(
        "/api/v1/opportunities/opportunity_b10_one/feedback",
        json={"decision": "dismissed"},
        headers={**viewer_headers, "Idempotency-Key": "b11-viewer-feedback"},
    )
    outcome = await client.post(
        "/api/v1/opportunities/opportunity_b10_one/trade-outcome",
        json={"days_to_sell": 1},
        headers={**viewer_headers, "Idempotency-Key": "b11-viewer-outcome"},
    )

    assert history.status_code == 200
    assert feedback.status_code == 403
    assert outcome.status_code == 403


async def test_b11_trade_outcome_requires_purchased_and_is_idempotent(
    b10_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = b10_client
    path = "/api/v1/opportunities/opportunity_b10_one"
    before_purchase = await client.post(
        f"{path}/trade-outcome",
        json={"days_to_sell": 12},
        headers={"Idempotency-Key": "b11-outcome-too-early"},
    )
    purchase = await client.post(
        f"{path}/feedback",
        json={"decision": "purchased"},
        headers={"Idempotency-Key": "b11-purchase-001"},
    )
    outcome_payload = {
        "acquisition_price": "1000.00",
        "acquisition_currency": "USD",
        "resale_price": "1400.00",
        "resale_currency": "USD",
        "actual_profit": "325.00",
        "days_to_sell": 12,
    }
    headers = {"Idempotency-Key": "b11-outcome-001"}
    created = await client.post(f"{path}/trade-outcome", json=outcome_payload, headers=headers)
    replay = await client.post(f"{path}/trade-outcome", json=outcome_payload, headers=headers)
    conflict = await client.post(
        f"{path}/trade-outcome",
        json={**outcome_payload, "days_to_sell": 13},
        headers=headers,
    )
    invalid_currency = await client.post(
        f"{path}/trade-outcome",
        json={"acquisition_price": "1000", "acquisition_currency": "usd"},
        headers={"Idempotency-Key": "b11-outcome-invalid"},
    )
    numeric_money = await client.post(
        f"{path}/trade-outcome",
        json={"acquisition_price": 1000.25, "acquisition_currency": "USD"},
        headers={"Idempotency-Key": "b11-outcome-numeric-money"},
    )

    assert before_purchase.status_code == 409
    assert purchase.status_code == 201, purchase.text
    assert created.status_code == 201
    assert created.json()["data"]["reference_id"] == "ref_b10"
    assert created.json()["data"]["actual_profit_currency"] == "USD"
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == created.json()["data"]["id"]
    assert conflict.status_code == 409
    assert invalid_currency.status_code == 422
    assert numeric_money.status_code == 422

    async with session_factory() as session:
        audit_events = list(
            (
                await session.scalars(
                    select(AuditEvent).where(AuditEvent.action == "trade_outcome.recorded")
                )
            ).all()
        )
        assert len(audit_events) == 1


async def test_b12_alert_rules_deliveries_and_test_notification_are_tenant_scoped(
    b10_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = b10_client
    rule_payload = {
        "name": "High margin watches",
        "filters": {
            "reference_ids": ["ref_b10"],
            "min_profit": "400.00",
            "conditions": ["excellent"],
        },
        "channels": ["push", "in_app"],
        "cooldown_minutes": 120,
    }
    async with session_factory() as session:
        session.add(
            AlertRule(
                id="rule_b12_other",
                organization_id=_OTHER_ORG_ID,
                created_by="usr_b10_user",
                name="Other tenant rule",
                filters={},
                channels=["push"],
            )
        )
        await session.commit()

    created = await client.post("/api/v1/alerts/rules", json=rule_payload)
    assert created.status_code == 201, created.text
    rule = created.json()["data"]
    rule_id = rule["id"]
    assert rule["filters"]["min_profit"] == "400.00"
    assert rule["channels"] == ["push", "in_app"]

    listed = await client.get("/api/v1/alerts/rules")
    fetched = await client.get(f"/api/v1/alerts/rules/{rule_id}")
    other_tenant = await client.get("/api/v1/alerts/rules/rule_b12_other")
    invalid_filter = await client.post(
        "/api/v1/alerts/rules",
        json={**rule_payload, "filters": {"min_profit": 400.0}},
    )
    updated = await client.put(
        f"/api/v1/alerts/rules/{rule_id}",
        json={**rule_payload, "name": "Updated rule"},
    )
    test_headers = {"Idempotency-Key": "b12-alert-test-001"}
    test_requested = await client.post(
        f"/api/v1/alerts/rules/{rule_id}/test",
        headers=test_headers,
    )
    test_replay = await client.post(
        f"/api/v1/alerts/rules/{rule_id}/test",
        headers=test_headers,
    )
    viewer_write = await client.post(
        "/api/v1/alerts/rules",
        json=rule_payload,
        headers={
            "Authorization": f"Bearer {issue_dev_token('b10-viewer')}",
            "X-Organization-ID": _ORG_ID,
        },
    )

    async with session_factory() as session:
        session.add_all(
            [
                AlertDelivery(
                    id="delivery_b12_owner",
                    organization_id=_ORG_ID,
                    rule_id=rule_id,
                    user_id="usr_b10_user",
                    opportunity_id="opportunity_b10_one",
                    material_version=1,
                    channel="push",
                    idempotency_key="delivery-b12-owner",
                    delivery_status="pending",
                ),
                AlertDelivery(
                    id="delivery_b12_viewer",
                    organization_id=_ORG_ID,
                    rule_id=rule_id,
                    user_id="usr_b10_viewer",
                    opportunity_id="opportunity_b10_one",
                    material_version=1,
                    channel="push",
                    idempotency_key="delivery-b12-viewer",
                    delivery_status="sent",
                ),
            ]
        )
        await session.commit()

    deliveries = await client.get(
        "/api/v1/alerts/deliveries",
        params={"rule_id": rule_id, "delivery_status": "pending"},
    )
    delete = await client.delete(f"/api/v1/alerts/rules/{rule_id}")
    deleted_rule = await client.get(f"/api/v1/alerts/rules/{rule_id}")
    disabled_test = await client.post(
        f"/api/v1/alerts/rules/{rule_id}/test",
        headers={"Idempotency-Key": "b12-alert-test-disabled"},
    )

    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [rule_id]
    assert fetched.status_code == 200
    assert other_tenant.status_code == 404
    assert invalid_filter.status_code == 422
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Updated rule"
    assert test_requested.status_code == 202
    assert test_replay.status_code == 200
    assert viewer_write.status_code == 403
    assert test_replay.json()["data"]["event_id"] == test_requested.json()["data"]["event_id"]
    assert deliveries.status_code == 200
    assert [item["id"] for item in deliveries.json()["data"]] == ["delivery_b12_owner"]
    assert delete.status_code == 204
    assert deleted_rule.json()["data"]["is_enabled"] is False
    assert disabled_test.status_code == 409

    async with session_factory() as session:
        test_events = list(
            (
                await session.scalars(
                    select(OutboxEvent).where(
                        OutboxEvent.event_name == "notification.test_requested"
                    )
                )
            ).all()
        )
        test_audits = list(
            (
                await session.scalars(
                    select(AuditEvent).where(AuditEvent.action == "alert_rule.test_requested")
                )
            ).all()
        )
        assert len(test_events) == 1
        assert test_events[0].status == "pending"
        assert len(test_audits) == 1


async def test_b12_activity_and_outcomes_are_organization_scoped(
    b10_client: tuple[AsyncClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, session_factory = b10_client
    async with session_factory() as session:
        session.add_all(
            [
                Feedback(
                    id="feedback_b12",
                    organization_id=_ORG_ID,
                    user_id="usr_b10_user",
                    opportunity_id="opportunity_b10_one",
                    decision="contacted",
                    notes="Called seller",
                    idempotency_key="feedback-b12",
                ),
                TradeOutcome(
                    id="outcome_b12",
                    organization_id=_ORG_ID,
                    user_id="usr_b10_user",
                    opportunity_id="opportunity_b10_one",
                    reference_id="ref_b10",
                    acquisition_price=Decimal("1000.00"),
                    acquisition_currency="USD",
                    actual_profit=Decimal("250.00"),
                    days_to_sell=14,
                    idempotency_key="outcome-b12",
                ),
                TradeOutcome(
                    id="outcome_b12_other",
                    organization_id=_OTHER_ORG_ID,
                    user_id="usr_b10_user",
                    opportunity_id=None,
                    reference_id="ref_b10",
                    actual_profit=Decimal("999.00"),
                    idempotency_key="outcome-b12-other",
                ),
            ]
        )
        await session.commit()

    activity = await client.get("/api/v1/activity")
    outcomes = await client.get("/api/v1/activity/outcomes")
    viewer_headers = {
        "Authorization": f"Bearer {issue_dev_token('b10-viewer')}",
        "X-Organization-ID": _ORG_ID,
    }
    viewer_activity = await client.get("/api/v1/activity", headers=viewer_headers)

    assert activity.status_code == 200
    assert {item["event_type"] for item in activity.json()["data"]} == {"feedback", "outcome"}
    assert all(item["id"] != "outcome_b12_other" for item in activity.json()["data"])
    assert outcomes.status_code == 200
    assert [item["id"] for item in outcomes.json()["data"]] == ["outcome_b12"]
    assert outcomes.json()["data"][0]["actual_profit_currency"] == "USD"
    assert viewer_activity.status_code == 200
