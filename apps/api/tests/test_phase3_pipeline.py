from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from apps.api.catalog.infrastructure.models import Brand, Reference, Source
from apps.api.identity.infrastructure.models import Organization
from apps.api.infrastructure.models import Base
from apps.api.listings.infrastructure.models import (
    DuplicateGroup,
    DuplicateGroupMember,
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.listings.infrastructure.repositories import (
    DuplicateRepository,
    ListingRepository,
)
from apps.api.valuation.infrastructure.models import (
    Opportunity,
    OpportunityView,
    Valuation,
)
from apps.api.valuation.infrastructure.repositories import (
    OpportunityRepository,
    ValuationRepository,
)
from sqlalchemy import Numeric, event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chronoarb.domain.ulid import generate_ulid


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def enable_fks(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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


class TestPhase3ModelParity:
    def test_listing_model_table_names(self):
        assert RawSnapshot.__tablename__ == "raw_snapshots"
        assert ParsedListing.__tablename__ == "parsed_listings"
        assert NormalizedListing.__tablename__ == "normalized_listings"
        assert DuplicateGroup.__tablename__ == "duplicate_groups"
        assert DuplicateGroupMember.__tablename__ == "duplicate_group_members"

    def test_valuation_and_opportunity_table_names(self):
        assert Valuation.__tablename__ == "valuations"
        assert Opportunity.__tablename__ == "opportunities"
        assert OpportunityView.__tablename__ == "opportunity_views"

    def test_normalized_listing_freshness_fields(self):
        assert NormalizedListing.__table__.c.observation_at.nullable is False
        assert NormalizedListing.__table__.c.fx_source.nullable is False
        assert NormalizedListing.__table__.c.fx_date.nullable is False
        assert "status" in NormalizedListing.__table__.c

    def test_valuation_money_columns_use_numeric(self):
        money_columns = (
            "expected_exit_price",
            "all_in_acquisition",
            "expected_net_resale",
            "expected_net_profit",
            "low_estimate",
            "high_estimate",
        )
        for name in money_columns:
            column_type = Valuation.__table__.c[name].type
            assert isinstance(column_type, Numeric)
            assert column_type.scale == 2

    def test_immutable_records_have_no_updated_at(self):
        assert "updated_at" not in RawSnapshot.__table__.c
        assert "updated_at" not in Valuation.__table__.c
        assert "updated_at" not in Opportunity.__table__.c

    def test_opportunity_is_tenant_scoped_and_versioned(self):
        assert Opportunity.__table__.c.organization_id.nullable is False
        assert Opportunity.__table__.c.material_version.nullable is False
        unique_names = {
            constraint.name
            for constraint in Opportunity.__table__.constraints
            if hasattr(constraint, "name") and constraint.name
        }
        assert "uq_opportunities_org_listing_version" in unique_names


async def seed_opportunity_chain(session: AsyncSession):
    brand = Brand(
        id=generate_ulid("brd"),
        name=f"Brand {generate_ulid('brd')}",
        slug=f"brand-{generate_ulid('brd')}",
    )
    source = Source(
        id=generate_ulid("src"),
        source_key=f"source-{generate_ulid('src')}",
        display_name="Test Source",
        adapter_version="1",
        access_mode="fixture",
    )
    organization = Organization(
        id=generate_ulid("org"),
        name="Test Organization",
        slug=f"org-{generate_ulid('org')}",
    )
    other_organization = Organization(
        id=generate_ulid("org"),
        name="Other Organization",
        slug=f"other-{generate_ulid('org')}",
    )
    session.add_all([brand, source, organization, other_organization])
    await session.flush()

    reference = Reference(
        id=generate_ulid("ref"),
        brand_id=brand.id,
        ref_code="REF-1",
        model_name="Test Model",
    )
    session.add(reference)
    await session.flush()

    snapshot = RawSnapshot(
        id=generate_ulid("raw"),
        source_id=source.id,
        external_id="external-1",
        adapter_version="1",
        checksum="checksum-1",
        raw_payload={"title": "Test"},
    )
    session.add(snapshot)
    await session.flush()

    parsed = ParsedListing(
        id=generate_ulid("lst"),
        snapshot_id=snapshot.id,
        parser_version="1",
        listing_price=Decimal("1000.00"),
        price_currency="USD",
    )
    session.add(parsed)
    await session.flush()

    normalized = NormalizedListing(
        id=generate_ulid("lst"),
        parsed_listing_id=parsed.id,
        reference_id=reference.id,
        normalization_version="1",
        normalized_price=Decimal("1000.00"),
        normalized_currency="USD",
        fx_rate=Decimal("1.00000000"),
        fx_source="fixture",
        fx_date=date(2026, 11, 5),
        observation_at=datetime.now(UTC),
        status="active",
        match_features={"confidence": 0.9},
    )
    session.add(normalized)
    await session.flush()

    valuation = Valuation(
        id=generate_ulid("val"),
        listing_id=normalized.id,
        model_version="1",
        config_version="1",
        cost_assumptions_version="1",
        expected_exit_price=Decimal("1400.00"),
        adjustment_details={"method": "fixture"},
    )
    session.add(valuation)
    await session.flush()

    return organization, other_organization, normalized, valuation


class TestPhase3Repositories:
    async def test_listing_and_duplicate_repository_reads(self, session):
        _organization, _other, normalized, _valuation = await seed_opportunity_chain(session)
        snapshot_result = await session.execute(select(RawSnapshot))
        snapshot = snapshot_result.scalars().first()
        assert snapshot is not None
        group = DuplicateGroup(
            id=generate_ulid("dup"),
            model_version="1",
            representative_id=normalized.id,
        )
        member = DuplicateGroupMember(
            id=generate_ulid("dpm"),
            group_id=group.id,
            listing_id=normalized.id,
        )
        session.add_all([group, member])
        await session.commit()

        listing_repo = ListingRepository(session)
        found_snapshot = await listing_repo.get_snapshot(
            snapshot.source_id,
            snapshot.external_id,
            snapshot.adapter_version,
            snapshot.checksum,
        )
        assert found_snapshot is not None

        duplicate_repo = DuplicateRepository(session)
        assert await duplicate_repo.get_group(group.id) is not None
        assert len(await duplicate_repo.list_members(group.id)) == 1

    async def test_opportunity_cursor_pagination_has_no_duplicates_or_gaps(self, session):
        organization, _other, normalized, valuation = await seed_opportunity_chain(session)
        base_time = datetime.now(UTC)
        opportunities = [
            Opportunity(
                id=generate_ulid("opp"),
                organization_id=organization.id,
                listing_id=normalized.id,
                valuation_id=valuation.id,
                material_version=index + 1,
                state="published",
                published_at=base_time - timedelta(minutes=index),
                positive_factors={"liquidity": "high"},
            )
            for index in range(3)
        ]
        session.add_all(opportunities)
        await session.commit()

        repository = OpportunityRepository(session)
        first_page, next_cursor = await repository.list_by_org(
            organization.id,
            limit=2,
        )
        assert len(first_page) == 2
        assert next_cursor is not None

        second_page, final_cursor = await repository.list_by_org(
            organization.id,
            limit=2,
            cursor=next_cursor,
        )
        assert len(second_page) == 1
        assert final_cursor is None
        ids = {item.id for item in first_page + second_page}
        assert len(ids) == 3

    async def test_opportunity_cross_tenant_returns_none(self, session):
        organization, other_organization, normalized, valuation = await seed_opportunity_chain(
            session
        )
        opportunity = Opportunity(
            id=generate_ulid("opp"),
            organization_id=organization.id,
            listing_id=normalized.id,
            valuation_id=valuation.id,
            material_version=1,
            state="published",
        )
        session.add(opportunity)
        await session.commit()

        repository = OpportunityRepository(session)
        assert await repository.get_by_id(opportunity.id, other_organization.id) is None

    async def test_valuation_repository_is_scoped_to_listing(self, session):
        _organization, _other, normalized, valuation = await seed_opportunity_chain(session)
        await session.commit()

        repository = ValuationRepository(session)
        found = await repository.get_for_listing(normalized.id)
        assert valuation.id in {item.id for item in found}
