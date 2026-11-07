from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from apps.api.alerts.infrastructure.models import AlertDelivery, AlertRule
from apps.api.alerts.infrastructure.repositories import (
    AlertDeliveryRepository,
    AlertRuleRepository,
)
from apps.api.billing.infrastructure.models import Subscription
from apps.api.billing.infrastructure.repositories import SubscriptionRepository
from apps.api.catalog.infrastructure.models import (
    Brand,
    Reference,
    Source,
    WatchList,
    WatchListEntry,
)
from apps.api.catalog.infrastructure.repositories import (
    ReferenceRepository,
    WatchListRepository,
)
from apps.api.feedback.infrastructure.models import Feedback, TradeOutcome
from apps.api.feedback.infrastructure.repositories import (
    FeedbackRepository,
    TradeOutcomeRepository,
)
from apps.api.identity.infrastructure.models import Organization, User
from apps.api.infrastructure.models import Base
from apps.api.infrastructure.pagination import decode_cursor, encode_cursor
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.operations.infrastructure.models import AuditEvent, FeatureFlag
from apps.api.operations.infrastructure.repositories import (
    AuditEventRepository,
    FeatureFlagRepository,
)
from apps.api.opportunities.infrastructure.models import Opportunity
from apps.api.opportunities.infrastructure.repositories import OpportunityRepository
from apps.api.valuation.infrastructure.models import Valuation
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chronoarb.domain.errors import ValidationError


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


async def add_listing(
    session: AsyncSession,
    reference: Reference,
    source: Source,
    suffix: str,
) -> tuple[NormalizedListing, Valuation]:
    snapshot = RawSnapshot(
        id=f"raw_{suffix}",
        source_id=source.id,
        external_id=f"external_{suffix}",
        adapter_version="1",
        checksum=f"checksum_{suffix}",
    )
    session.add(snapshot)
    await session.flush()
    parsed = ParsedListing(
        id=f"parsed_{suffix}",
        snapshot_id=snapshot.id,
        parser_version="1",
        listing_price=Decimal("1000.00"),
        price_currency="USD",
        listing_title=f"Listing {suffix}",
    )
    session.add(parsed)
    await session.flush()
    listing = NormalizedListing(
        id=f"listing_{suffix}",
        parsed_listing_id=parsed.id,
        reference_id=reference.id,
        normalization_version="1",
        condition="excellent",
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
        id=f"valuation_{suffix}",
        listing_id=listing.id,
        model_version="valuation-v1",
        config_version="config-v1",
        cost_assumptions_version="ca-2026.1-sample",
        expected_exit_price=Decimal("1500.00"),
        all_in_acquisition=Decimal("1100.00"),
        expected_net_profit=Decimal("300.00"),
        roi=Decimal("0.2727"),
        confidence=Decimal("0.9000"),
    )
    session.add(valuation)
    await session.flush()
    return listing, valuation


async def add_opportunity(
    session: AsyncSession,
    organization_id: str,
    listing: NormalizedListing,
    valuation: Valuation,
    *,
    id: str,
    version: int = 1,
) -> Opportunity:
    opportunity = Opportunity(
        id=id,
        organization_id=organization_id,
        listing_id=listing.id,
        valuation_id=valuation.id,
        material_version=version,
        score=Decimal("0.7500"),
        state="published",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        positive_factors=["price"],
        negative_factors=[],
    )
    session.add(opportunity)
    await session.flush()
    return opportunity


async def seed_repository_tenants(
    session: AsyncSession,
) -> tuple[str, str, str, str, str]:
    brand = Brand(id="brand", name="Example", slug="example")
    reference = Reference(
        id="reference",
        brand_id=brand.id,
        ref_code="EX-1",
        model_name="Example Watch",
    )
    source = Source(
        id="source",
        source_key="fixture",
        display_name="Fixture Source",
        adapter_version="1",
        access_mode="fixture",
    )
    org_a = Organization(id="org_a", name="Org A", slug="org-a")
    org_b = Organization(id="org_b", name="Org B", slug="org-b")
    user_a = User(id="user_a", cognito_sub="dev|user_a", email="a@example.test")
    user_b = User(id="user_b", cognito_sub="dev|user_b", email="b@example.test")
    session.add_all([brand, reference, source, org_a, org_b, user_a, user_b])
    await session.flush()

    listing, valuation = await add_listing(session, reference, source, "tenant")
    opportunity_a = await add_opportunity(session, org_a.id, listing, valuation, id="opportunity_a")
    opportunity_b = await add_opportunity(session, org_b.id, listing, valuation, id="opportunity_b")
    watch_a = WatchList(id="watch_a", organization_id=org_a.id, name="A")
    watch_b = WatchList(id="watch_b", organization_id=org_b.id, name="B")
    session.add_all([watch_a, watch_b])
    await session.flush()
    session.add_all(
        [
            WatchListEntry(id="entry_a", watch_list_id=watch_a.id, reference_id=reference.id),
            WatchListEntry(id="entry_b", watch_list_id=watch_b.id, reference_id=reference.id),
        ]
    )

    rule_a = AlertRule(
        id="rule_a",
        organization_id=org_a.id,
        created_by=user_a.id,
        name="A",
        filters={},
        channels=["in_app"],
    )
    rule_b = AlertRule(
        id="rule_b",
        organization_id=org_b.id,
        created_by=user_b.id,
        name="B",
        filters={},
        channels=["in_app"],
    )
    session.add_all([rule_a, rule_b])
    await session.flush()
    session.add_all(
        [
            Feedback(
                id="feedback_a",
                organization_id=org_a.id,
                user_id=user_a.id,
                opportunity_id=opportunity_a.id,
                decision="contacted",
                idempotency_key="org_a:user_a:feedback",
            ),
            Feedback(
                id="feedback_b",
                organization_id=org_b.id,
                user_id=user_b.id,
                opportunity_id=opportunity_b.id,
                decision="contacted",
                idempotency_key="org_b:user_b:feedback",
            ),
            TradeOutcome(
                id="outcome_a",
                organization_id=org_a.id,
                user_id=user_a.id,
                opportunity_id=opportunity_a.id,
                reference_id=reference.id,
                idempotency_key="org_a:user_a:outcome",
            ),
            TradeOutcome(
                id="outcome_b",
                organization_id=org_b.id,
                user_id=user_b.id,
                opportunity_id=opportunity_b.id,
                reference_id=reference.id,
                idempotency_key="org_b:user_b:outcome",
            ),
            AlertDelivery(
                id="delivery_a",
                organization_id=org_a.id,
                rule_id=rule_a.id,
                user_id=user_a.id,
                opportunity_id=opportunity_a.id,
                material_version=1,
                channel="in_app",
                idempotency_key="org_a:user_a:delivery",
                delivery_status="pending",
            ),
            AlertDelivery(
                id="delivery_b",
                organization_id=org_b.id,
                rule_id=rule_b.id,
                user_id=user_b.id,
                opportunity_id=opportunity_b.id,
                material_version=1,
                channel="in_app",
                idempotency_key="org_b:user_b:delivery",
                delivery_status="pending",
            ),
            Subscription(id="subscription_a", organization_id=org_a.id, status="trialing"),
            Subscription(id="subscription_b", organization_id=org_b.id, status="trialing"),
            AuditEvent(
                id="audit_a",
                organization_id=org_a.id,
                user_id=user_a.id,
                action="test",
                resource_type="test",
                resource_id="a",
            ),
            AuditEvent(
                id="audit_b",
                organization_id=org_b.id,
                user_id=user_b.id,
                action="test",
                resource_type="test",
                resource_id="b",
            ),
        ]
    )
    await session.commit()
    return org_a.id, org_b.id, opportunity_a.id, opportunity_b.id, listing.id


class TestCursorPagination:
    def test_round_trip(self):
        encoded = encode_cursor("score_desc", "0.7500", "opp_123")
        assert decode_cursor(encoded) == ("score_desc", "0.7500", "opp_123")

    @pytest.mark.parametrize("cursor", ["", "not-base64!", "e30", "e30="])
    def test_malformed_cursor_raises_validation_error(self, cursor):
        with pytest.raises(ValidationError):
            decode_cursor(cursor)

    def test_tampered_cursor_raises_validation_error(self):
        cursor = encode_cursor("newest", "2026-01-01T00:00:00+00:00", "opp_123")
        replacement = "A" if cursor[0] != "A" else "B"
        with pytest.raises(ValidationError):
            decode_cursor(replacement + cursor[1:])


class TestOpportunityRepository:
    async def test_feed_orders_stably_across_pages_and_hides_old_versions(self, session):
        org = Organization(id="feed_org", name="Feed Org", slug="feed-org")
        brand = Brand(id="feed_brand", name="Feed Brand", slug="feed-brand")
        reference = Reference(id="feed_ref", brand_id=brand.id, ref_code="F-1")
        source = Source(
            id="feed_source",
            source_key="feed",
            display_name="Feed",
            adapter_version="1",
            access_mode="fixture",
        )
        session.add_all([org, brand, reference, source])
        await session.flush()

        for index in range(25):
            listing, valuation = await add_listing(session, reference, source, f"feed{index:02}")
            if index == 0:
                await add_opportunity(
                    session,
                    org.id,
                    listing,
                    valuation,
                    id="feed_old_version",
                )
                await add_opportunity(
                    session,
                    org.id,
                    listing,
                    valuation,
                    id="feed_latest_version",
                    version=2,
                )
            else:
                await add_opportunity(
                    session,
                    org.id,
                    listing,
                    valuation,
                    id=f"feed_{index:02}",
                )
        await session.commit()

        repository = OpportunityRepository(session)
        first_page = await repository.list_feed(org.id, limit=7, sort="score_desc")
        all_ids = [item["id"] for item in first_page.items]
        cursor = first_page.next_cursor
        while cursor is not None:
            page = await repository.list_feed(org.id, limit=7, sort="score_desc", cursor=cursor)
            all_ids.extend(item["id"] for item in page.items)
            cursor = page.next_cursor

        assert len(all_ids) == 25
        assert all_ids == sorted(all_ids)
        assert "feed_latest_version" in all_ids
        assert "feed_old_version" not in all_ids
        assert first_page.has_more

        assert await repository.get_by_id("feed_old_version", org.id) is None
        versions = await repository.list_versions("listing_feed00", org.id)
        assert [version.material_version for version in versions] == [2, 1]

    async def test_feed_statement_count_is_bounded(self, session):
        org_id, _, _, _, _ = await seed_repository_tenants(session)
        statements = 0

        def count_statements(*_args):
            nonlocal statements
            statements += 1

        event.listen(session.bind.sync_engine, "before_cursor_execute", count_statements)
        try:
            page = await OpportunityRepository(session).list_feed(org_id, limit=25)
        finally:
            event.remove(session.bind.sync_engine, "before_cursor_execute", count_statements)
        assert len(page.items) == 1
        assert statements <= 3

    async def test_tenant_repository_reads_are_scoped(self, session):
        org_a, org_b, opportunity_a, _, _ = await seed_repository_tenants(session)

        assert await OpportunityRepository(session).get_by_id(opportunity_a, org_b) is None
        assert await FeedbackRepository(session).get_by_id("feedback_a", org_b) is None
        assert await TradeOutcomeRepository(session).get_by_id("outcome_a", org_b) is None
        assert await AlertRuleRepository(session).get_by_id("rule_a", org_b) is None
        assert await AlertDeliveryRepository(session).get_by_id("delivery_a", org_b) is None
        assert await WatchListRepository(session).get_by_id("watch_a", org_b) is None
        assert await SubscriptionRepository(session).get_by_id("subscription_a", org_b) is None
        assert await AuditEventRepository(session).get_by_id("audit_a", org_b) is None
        audit_events = await AuditEventRepository(session).list_by_org(org_b)
        assert [audit_event.id for audit_event in audit_events] == ["audit_b"]

        assert (
            len(await FeedbackRepository(session).list_for_opportunity(opportunity_a, org_a)) == 1
        )

    async def test_feed_filters_are_tenant_scoped(self, session):
        org_a, org_b, _, _, _ = await seed_repository_tenants(session)
        repository = OpportunityRepository(session)

        own_watch_list = await repository.list_feed(
            org_a, watch_list_id="watch_a", condition="excellent"
        )
        other_tenant_watch_list = await repository.list_feed(org_a, watch_list_id="watch_b")
        other_tenant_feed = await repository.list_feed(org_b, watch_list_id="watch_a")
        personalized_feed = await repository.list_feed(org_a, user_id="user_a")

        assert len(own_watch_list.items) == 1
        assert other_tenant_watch_list.items == []
        assert other_tenant_feed.items == []
        assert personalized_feed.items[0]["my_decision"] == "contacted"

    async def test_reference_search_pagination_and_global_flags(self, session):
        brand = Brand(id="refs_brand", name="Refs", slug="refs")
        session.add(brand)
        session.add_all(
            [
                Reference(id="ref_a", brand_id=brand.id, ref_code="A"),
                Reference(id="ref_b", brand_id=brand.id, ref_code="B"),
                Reference(id="ref_c", brand_id=brand.id, ref_code="C"),
            ]
        )
        session.add_all(
            [
                FeatureFlag(id="flag_a", key="alpha"),
                FeatureFlag(id="flag_b", key="beta"),
            ]
        )
        await session.commit()

        repository = ReferenceRepository(session)
        first = await repository.search(limit=2)
        second = await repository.search(limit=2, cursor=first.next_cursor)
        assert [item.ref_code for item in first.items + second.items] == ["A", "B", "C"]
        flags = await FeatureFlagRepository(session).list_all()
        assert [flag.key for flag in flags] == ["alpha", "beta"]
