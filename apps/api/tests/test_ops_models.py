from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from apps.api.alerts.infrastructure.models import AlertDelivery, AlertRule
from apps.api.billing.infrastructure.models import Subscription
from apps.api.catalog.infrastructure.models import Brand, Reference, Source
from apps.api.feedback.infrastructure.models import Feedback, TradeOutcome
from apps.api.identity.infrastructure.models import Organization, User
from apps.api.infrastructure.models import Base
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.operations.infrastructure.models import AuditEvent, FeatureFlag, OutboxEvent
from apps.api.opportunities.infrastructure.models import Opportunity
from apps.api.valuation.infrastructure.models import Valuation
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def enable_fks(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with sessionmaker() as db_session:
        yield db_session
    await engine.dispose()


async def create_alert_delivery_dependencies(session: AsyncSession) -> tuple[str, str, str]:
    brand = Brand(id="brd_ops", name="Ops Example", slug="ops-example")
    reference = Reference(id="ref_ops", brand_id=brand.id, ref_code="OPS-1")
    source = Source(
        id="src_ops",
        source_key="ops-example",
        display_name="Ops Example",
        adapter_version="1",
        access_mode="fixture",
    )
    organization = Organization(id="org_ops", name="Ops Org", slug="ops-org")
    user = User(id="usr_ops", cognito_sub="dev|usr_ops", email="ops@example.test")
    session.add_all([brand, reference, source, organization, user])
    await session.flush()

    snapshot = RawSnapshot(
        id="raw_ops",
        source_id=source.id,
        external_id="listing-ops",
        adapter_version="1",
        checksum="ops-checksum",
    )
    session.add(snapshot)
    await session.flush()
    parsed = ParsedListing(
        id="parsed_ops",
        snapshot_id=snapshot.id,
        parser_version="1",
    )
    session.add(parsed)
    await session.flush()
    listing = NormalizedListing(
        id="norm_ops",
        parsed_listing_id=parsed.id,
        reference_id=reference.id,
        normalization_version="1",
        fx_rate=Decimal("1"),
        fx_source="identity",
        fx_date=date(2026, 1, 1),
        observation_at=datetime(2026, 1, 1, tzinfo=UTC),
        status="active",
    )
    session.add(listing)
    await session.flush()
    valuation = Valuation(
        id="val_ops",
        listing_id=listing.id,
        model_version="1",
        config_version="1",
        cost_assumptions_version="1",
    )
    session.add(valuation)
    await session.flush()
    opportunity = Opportunity(
        id="opp_ops",
        organization_id=organization.id,
        listing_id=listing.id,
        valuation_id=valuation.id,
        material_version=1,
        state="published",
    )
    session.add(opportunity)
    rule = AlertRule(
        id="rule_ops",
        organization_id=organization.id,
        created_by=user.id,
        name="Ops rule",
        filters={},
        channels=["in_app"],
    )
    session.add_all([opportunity, rule])
    await session.commit()
    return organization.id, user.id, opportunity.id


class TestOperationsOrmParity:
    @pytest.mark.parametrize(
        ("model", "expected_columns"),
        [
            (
                AlertRule,
                {
                    "id": False,
                    "organization_id": False,
                    "created_by": False,
                    "name": False,
                    "filters": False,
                    "channels": False,
                    "cooldown_minutes": False,
                    "is_enabled": False,
                    "created_at": False,
                    "updated_at": False,
                },
            ),
            (
                AlertDelivery,
                {
                    "id": False,
                    "organization_id": False,
                    "rule_id": False,
                    "user_id": False,
                    "opportunity_id": False,
                    "material_version": False,
                    "channel": False,
                    "idempotency_key": False,
                    "delivery_status": False,
                    "provider_message_id": True,
                    "created_at": False,
                },
            ),
            (
                Feedback,
                {
                    "id": False,
                    "organization_id": False,
                    "user_id": False,
                    "opportunity_id": False,
                    "decision": False,
                    "notes": True,
                    "idempotency_key": False,
                    "created_at": False,
                },
            ),
            (
                TradeOutcome,
                {
                    "id": False,
                    "organization_id": False,
                    "user_id": False,
                    "opportunity_id": True,
                    "reference_id": False,
                    "acquisition_price": True,
                    "acquisition_currency": True,
                    "resale_price": True,
                    "resale_currency": True,
                    "actual_profit": True,
                    "days_to_sell": True,
                    "idempotency_key": False,
                    "created_at": False,
                },
            ),
            (
                Subscription,
                {
                    "id": False,
                    "organization_id": False,
                    "stripe_customer_id": True,
                    "stripe_subscription_id": True,
                    "status": False,
                    "plan_id": True,
                    "current_period_start": True,
                    "current_period_end": True,
                    "trial_end": True,
                    "created_at": False,
                    "updated_at": False,
                },
            ),
            (
                AuditEvent,
                {
                    "id": False,
                    "organization_id": True,
                    "user_id": True,
                    "action": False,
                    "resource_type": False,
                    "resource_id": False,
                    "details": True,
                    "trace_id": True,
                    "client_ip": True,
                    "created_at": False,
                },
            ),
            (
                OutboxEvent,
                {
                    "id": False,
                    "event_name": False,
                    "event_version": False,
                    "payload": False,
                    "trace_id": True,
                    "status": False,
                    "created_at": False,
                    "published_at": True,
                },
            ),
            (
                FeatureFlag,
                {
                    "id": False,
                    "key": False,
                    "description": True,
                    "enabled": False,
                    "organization_ids": True,
                    "rollout_pct": False,
                    "expires_at": True,
                    "created_at": False,
                },
            ),
        ],
    )
    def test_columns_and_nullability_match_migration(self, model, expected_columns):
        columns = model.__table__.c
        assert set(columns.keys()) == set(expected_columns)
        assert {name: columns[name].nullable for name in expected_columns} == expected_columns

    def test_idempotency_keys_are_globally_unique(self):
        for model, constraint_name in (
            (AlertDelivery, "uq_alert_deliveries_idempotency_key"),
            (Feedback, "uq_feedbacks_idempotency_key"),
            (TradeOutcome, "uq_trade_outcomes_idempotency_key"),
        ):
            unique_constraints = [
                constraint
                for constraint in model.__table__.constraints
                if constraint.name == constraint_name
            ]
            assert len(unique_constraints) == 1
            assert [column.name for column in unique_constraints[0].columns] == ["idempotency_key"]

    async def test_idempotency_keys_are_enforced_by_database(self, session):
        organization_id, user_id, opportunity_id = await create_alert_delivery_dependencies(session)
        duplicate_rows = (
            (
                Feedback(
                    id="feedback_one",
                    organization_id=organization_id,
                    user_id=user_id,
                    opportunity_id=opportunity_id,
                    decision="purchased",
                    idempotency_key="same-feedback-key",
                ),
                Feedback(
                    id="feedback_two",
                    organization_id=organization_id,
                    user_id=user_id,
                    opportunity_id=opportunity_id,
                    decision="contacted",
                    idempotency_key="same-feedback-key",
                ),
            ),
            (
                TradeOutcome(
                    id="outcome_one",
                    organization_id=organization_id,
                    user_id=user_id,
                    opportunity_id=opportunity_id,
                    reference_id="ref_ops",
                    idempotency_key="same-outcome-key",
                ),
                TradeOutcome(
                    id="outcome_two",
                    organization_id=organization_id,
                    user_id=user_id,
                    opportunity_id=opportunity_id,
                    reference_id="ref_ops",
                    idempotency_key="same-outcome-key",
                ),
            ),
            (
                AlertDelivery(
                    id="delivery_one",
                    organization_id=organization_id,
                    rule_id="rule_ops",
                    user_id=user_id,
                    opportunity_id=opportunity_id,
                    material_version=1,
                    channel="in_app",
                    idempotency_key="same-delivery-key",
                    delivery_status="pending",
                ),
                AlertDelivery(
                    id="delivery_two",
                    organization_id=organization_id,
                    rule_id="rule_ops",
                    user_id=user_id,
                    opportunity_id=opportunity_id,
                    material_version=1,
                    channel="in_app",
                    idempotency_key="same-delivery-key",
                    delivery_status="pending",
                ),
            ),
        )
        for first, duplicate in duplicate_rows:
            session.add(first)
            await session.commit()
            session.add(duplicate)
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()
