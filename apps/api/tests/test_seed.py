from __future__ import annotations

import pytest
from apps.api.alerts.api.schemas import AlertRuleCreateRequest
from apps.api.alerts.infrastructure.models import AlertDelivery, AlertRule
from apps.api.billing.infrastructure.models import Subscription
from apps.api.catalog.infrastructure.models import Brand, Reference, Source
from apps.api.feedback.infrastructure.models import Feedback, TradeOutcome
from apps.api.identity.infrastructure.models import Membership, Organization, User
from apps.api.infrastructure.models import Base
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.operations.infrastructure.models import AuditEvent, FeatureFlag
from apps.api.opportunities.infrastructure.models import Opportunity
from apps.api.seed.data import seed_data_summary
from apps.api.seed.runner import reset_and_seed, seed_database
from apps.api.valuation.infrastructure.models import Valuation
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def enable_fks(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with sessionmaker() as s:
        yield s
    await engine.dispose()


class TestSeedData:
    def test_seed_data_summary_non_empty(self):
        summary = seed_data_summary()
        assert "organizations=" in summary
        assert "users=" in summary
        assert "memberships=" in summary
        assert "brands=" in summary
        assert "sources=" in summary
        assert "references=" in summary

    def test_seed_organizations_have_slugs(self):
        from apps.api.seed.data import SEED_ORGANIZATIONS

        assert len(SEED_ORGANIZATIONS) >= 2
        for org in SEED_ORGANIZATIONS:
            assert org.slug
            assert org.name
            assert "-" not in org.slug.split("-")[0] or org.slug.startswith(org.slug.split("-")[0])

    def test_seed_users_have_required_fields(self):
        from apps.api.seed.data import SEED_USERS

        assert len(SEED_USERS) >= 3
        for user in SEED_USERS:
            assert user.cognito_sub
            assert user.email
            assert "@" in user.email

    def test_seed_brands_have_required_fields(self):
        from apps.api.seed.data import SEED_BRANDS

        assert len(SEED_BRANDS) >= 3
        for brand in SEED_BRANDS:
            assert brand.name
            assert brand.slug

    def test_seed_sources_have_required_fields(self):
        from apps.api.seed.data import SEED_SOURCES

        assert len(SEED_SOURCES) >= 3
        for source in SEED_SOURCES:
            assert source.source_key
            assert source.display_name
            assert source.adapter_version
            assert source.access_mode

    def test_seed_references_link_to_brands(self):
        from apps.api.seed.data import SEED_BRANDS, SEED_REFERENCES

        brand_slugs = {b.slug for b in SEED_BRANDS}
        for ref in SEED_REFERENCES:
            assert ref.brand_slug in brand_slugs
            assert ref.ref_code


class TestSeedDatabase:
    async def test_seed_creates_organizations(self, session):
        counts = await seed_database(session)

        assert counts["organizations"] == 2
        result = await session.execute(select(Organization))
        orgs = result.scalars().all()
        assert len(orgs) == 2
        slugs = {o.slug for o in orgs}
        assert "demo" in slugs
        assert "acme-watch" in slugs

    async def test_seed_creates_users(self, session):
        counts = await seed_database(session)

        assert counts["users"] == 5
        result = await session.execute(select(User))
        users = result.scalars().all()
        assert len(users) == 5
        emails = {u.email for u in users}
        assert "owner@demo.example.com" in emails
        assert "dealer@demo.example.com" in emails
        assert "viewer@demo.example.com" in emails
        assert "owner@acme.example.com" in emails
        assert "ops@chronoarb.example.com" in emails

    async def test_seed_creates_brands(self, session):
        counts = await seed_database(session)

        assert counts["brands"] == 6
        result = await session.execute(select(Brand))
        brands = result.scalars().all()
        assert len(brands) == 6
        slugs = {b.slug for b in brands}
        assert "rolex" in slugs
        assert "omega" in slugs
        assert "patek-philippe" in slugs

    async def test_seed_creates_sources(self, session):
        counts = await seed_database(session)

        assert counts["sources"] == 5
        result = await session.execute(select(Source))
        sources = result.scalars().all()
        assert len(sources) == 5
        keys = {s.source_key for s in sources}
        assert "ebay" in keys
        assert "chrono24" in keys
        assert "watchbox" in keys
        assert "christies" in keys
        assert "sothebys" in keys

    async def test_seed_creates_references(self, session):
        counts = await seed_database(session)

        assert counts["references"] == 15
        result = await session.execute(select(Reference))
        refs = result.scalars().all()
        assert len(refs) == 15

    async def test_seed_creates_memberships(self, session):
        counts = await seed_database(session)

        assert counts["memberships"] == 4
        result = await session.execute(select(Membership))
        memberships = result.scalars().all()
        assert len(memberships) == 4

    async def test_seed_references_link_to_brands(self, session):
        await seed_database(session)

        result = await session.execute(select(Reference))
        refs = result.scalars().all()
        result = await session.execute(select(Brand))
        brands = result.scalars().all()
        brand_ids = {b.id for b in brands}
        for ref in refs:
            assert ref.brand_id in brand_ids

    async def test_seed_is_idempotent(self, session):
        counts1 = await seed_database(session)
        counts2 = await seed_database(session)

        assert counts1 == counts2
        result = await session.execute(select(Organization))
        assert len(result.scalars().all()) == 2

    async def test_reset_and_seed(self, session):
        await seed_database(session)
        counts = await reset_and_seed(session)

        assert counts["organizations"] == 2
        assert counts["users"] == 5
        result = await session.execute(select(Organization))
        assert len(result.scalars().all()) == 2


class TestSeedDataSummaryExtended:
    def test_seed_data_summary_includes_listing_entities(self):
        summary = seed_data_summary()
        assert "snapshots=" in summary
        assert "parsed_listings=" in summary
        assert "normalized_listings=" in summary
        assert "valuations=" in summary
        assert "opportunities=" in summary
        assert "alert_rules=" in summary
        assert "alert_deliveries=" in summary
        assert "feedback=" in summary
        assert "trade_outcomes=" in summary
        assert "subscriptions=" in summary
        assert "feature_flags=" in summary
        assert "audit_events=" in summary


class TestSeedDatabaseExtended:
    async def test_seed_creates_snapshots(self, session):
        counts = await seed_database(session)

        assert counts["snapshots"] == 4
        result = await session.execute(select(RawSnapshot))
        assert len(result.scalars().all()) == 4

    async def test_seed_creates_parsed_listings(self, session):
        counts = await seed_database(session)

        assert counts["parsed_listings"] == 4
        result = await session.execute(select(ParsedListing))
        assert len(result.scalars().all()) == 4

    async def test_seed_creates_normalized_listings(self, session):
        counts = await seed_database(session)

        assert counts["normalized_listings"] == 4
        result = await session.execute(select(NormalizedListing))
        assert len(result.scalars().all()) == 4

    async def test_seed_creates_valuations(self, session):
        counts = await seed_database(session)

        assert counts["valuations"] == 4
        result = await session.execute(select(Valuation))
        assert len(result.scalars().all()) == 4

    async def test_seed_creates_opportunities(self, session):
        counts = await seed_database(session)

        assert counts["opportunities"] == 5
        result = await session.execute(select(Opportunity))
        opps = result.scalars().all()
        assert len(opps) == 5
        states = {o.state for o in opps}
        assert states == {"published", "purchased", "contacted"}

    async def test_seed_links_chain(self, session):
        await seed_database(session)

        snapshots = (await session.execute(select(RawSnapshot))).scalars().all()
        assert len(snapshots) == 4

        parsed = (await session.execute(select(ParsedListing))).scalars().all()
        assert len(parsed) == 4
        parsed_snapshot_ids = {p.snapshot_id for p in parsed}
        assert parsed_snapshot_ids == {s.id for s in snapshots}

        normalized = (await session.execute(select(NormalizedListing))).scalars().all()
        assert len(normalized) == 4
        norm_parsed_ids = {n.parsed_listing_id for n in normalized}
        assert norm_parsed_ids == {p.id for p in parsed}

        valuations = (await session.execute(select(Valuation))).scalars().all()
        assert len(valuations) == 4
        val_listing_ids = {v.listing_id for v in valuations}
        assert val_listing_ids == {n.id for n in normalized}

        opps = (await session.execute(select(Opportunity))).scalars().all()
        assert len(opps) == 5
        opp_listing_ids = {o.listing_id for o in opps}
        assert opp_listing_ids <= {n.id for n in normalized}
        opp_valuation_ids = {o.valuation_id for o in opps}
        assert opp_valuation_ids <= {v.id for v in valuations}

    async def test_seed_opportunities_link_to_orgs(self, session):
        await seed_database(session)

        orgs = (await session.execute(select(Organization))).scalars().all()
        org_ids = {o.id for o in orgs}
        opps = (await session.execute(select(Opportunity))).scalars().all()
        for opp in opps:
            assert opp.organization_id in org_ids

    async def test_seed_is_idempotent_extended(self, session):
        counts1 = await seed_database(session)
        counts2 = await seed_database(session)

        assert counts1 == counts2
        result = await session.execute(select(RawSnapshot))
        assert len(result.scalars().all()) == 4
        result = await session.execute(select(Opportunity))
        assert len(result.scalars().all()) == 5

    async def test_reset_and_seed_extended(self, session):
        await seed_database(session)
        counts = await reset_and_seed(session)

        assert counts["snapshots"] == 4
        assert counts["parsed_listings"] == 4
        assert counts["normalized_listings"] == 4
        assert counts["valuations"] == 4
        assert counts["opportunities"] == 5
        result = await session.execute(select(Opportunity))
        assert len(result.scalars().all()) == 5


class TestSeedDatabaseB16:
    async def test_seed_creates_b16_records_and_valid_relationships(self, session):
        counts = await seed_database(session)

        assert counts["alert_rules"] == 2
        assert counts["alert_deliveries"] == 2
        assert counts["feedback"] == 2
        assert counts["trade_outcomes"] == 1
        assert counts["subscriptions"] == 2
        assert counts["feature_flags"] == 3
        assert counts["audit_events"] == 2

        rules = list((await session.scalars(select(AlertRule))).all())
        deliveries = list((await session.scalars(select(AlertDelivery))).all())
        feedback = list((await session.scalars(select(Feedback))).all())
        outcomes = list((await session.scalars(select(TradeOutcome))).all())
        subscriptions = list((await session.scalars(select(Subscription))).all())
        flags = list((await session.scalars(select(FeatureFlag))).all())
        audit_events = list((await session.scalars(select(AuditEvent))).all())
        opportunities = {
            opportunity.id: opportunity
            for opportunity in (await session.scalars(select(Opportunity))).all()
        }
        org_ids = {
            organization.slug: organization.id
            for organization in (await session.scalars(select(Organization))).all()
        }

        assert len(rules) == len(deliveries) == 2
        assert len(feedback) == len(subscriptions) == len(audit_events) == 2
        assert len(outcomes) == 1
        assert len(flags) == 3
        assert {item.state for item in opportunities.values()} == {
            "published",
            "purchased",
            "contacted",
        }
        assert all(item.rule_id in {rule.id for rule in rules} for item in deliveries)
        assert all(item.opportunity_id in opportunities for item in deliveries)
        assert all(opportunities[item.opportunity_id].state == item.decision for item in feedback)
        assert outcomes[0].opportunity_id in opportunities
        assert outcomes[0].reference_id is not None
        assert outcomes[0].actual_profit == 900
        assert {item.status for item in subscriptions} == {"active", "trialing"}
        assert next(flag for flag in flags if flag.key == "valuation.v2").organization_ids == [
            org_ids["demo"]
        ]
        assert all(item.organization_id in org_ids.values() for item in audit_events)
        for rule in rules:
            AlertRuleCreateRequest.model_validate(
                {
                    "name": rule.name,
                    "filters": rule.filters,
                    "channels": rule.channels,
                    "cooldown_minutes": rule.cooldown_minutes,
                    "is_enabled": rule.is_enabled,
                }
            )

    async def test_b16_seed_is_idempotent(self, session):
        first_counts = await seed_database(session)
        second_counts = await seed_database(session)

        assert first_counts == second_counts
        assert len(list((await session.scalars(select(AlertRule))).all())) == 2
        assert len(list((await session.scalars(select(AlertDelivery))).all())) == 2
        assert len(list((await session.scalars(select(Feedback))).all())) == 2
        assert len(list((await session.scalars(select(TradeOutcome))).all())) == 1
        assert len(list((await session.scalars(select(Subscription))).all())) == 2
        assert len(list((await session.scalars(select(FeatureFlag))).all())) == 3
        assert len(list((await session.scalars(select(AuditEvent))).all())) == 2

    async def test_b16_reset_deletes_and_recreates_dependent_records(self, session):
        await seed_database(session)
        counts = await reset_and_seed(session)

        assert counts["alert_rules"] == 2
        assert counts["alert_deliveries"] == 2
        assert counts["feedback"] == 2
        assert counts["trade_outcomes"] == 1
        assert counts["subscriptions"] == 2
        assert counts["feature_flags"] == 3
        assert counts["audit_events"] == 2
        assert len(list((await session.scalars(select(AlertDelivery))).all())) == 2
        assert len(list((await session.scalars(select(Feedback))).all())) == 2
        assert len(list((await session.scalars(select(TradeOutcome))).all())) == 1
