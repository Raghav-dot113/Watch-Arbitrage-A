from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from apps.api.catalog.infrastructure.models import Brand, Reference, Source
from apps.api.duplicates.infrastructure.models import DuplicateGroup, DuplicateGroupMember
from apps.api.identity.infrastructure import models as _identity_models  # noqa: F401
from apps.api.identity.infrastructure.models import Organization, User
from apps.api.infrastructure.models import Base
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
from apps.api.opportunities.infrastructure.models import Opportunity, OpportunityView
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


async def create_opportunity_dependencies(session: AsyncSession) -> Opportunity:
    brand = Brand(id="brd_test", name="Example", slug="example")
    reference = Reference(id="ref_test", brand_id=brand.id, ref_code="EX-1")
    source = Source(
        id="src_test",
        source_key="example",
        display_name="Example",
        adapter_version="1",
        access_mode="fixture",
    )
    organization = Organization(id="org_test", name="Example Org", slug="example-org")
    user = User(id="usr_test", cognito_sub="dev|usr_test", email="test@example.test")
    session.add_all([brand, reference, source, organization, user])
    await session.flush()

    snapshot = RawSnapshot(
        id="raw_test",
        source_id=source.id,
        external_id="listing-1",
        adapter_version="1",
        checksum="abc123",
    )
    session.add(snapshot)
    await session.flush()
    parsed = ParsedListing(
        id="parsed_test",
        snapshot_id=snapshot.id,
        parser_version="1",
    )
    session.add(parsed)
    await session.flush()
    listing = NormalizedListing(
        id="norm_test",
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
        id="val_test",
        listing_id=listing.id,
        model_version="1",
        config_version="1",
        cost_assumptions_version="1",
        expected_exit_price=Decimal("12000.00"),
    )
    session.add(valuation)
    await session.flush()
    opportunity = Opportunity(
        id="opp_test",
        organization_id=organization.id,
        listing_id=listing.id,
        valuation_id=valuation.id,
        material_version=1,
        state="published",
    )
    session.add(opportunity)
    await session.flush()
    return opportunity


class TestOpportunityOrmParity:
    @pytest.mark.parametrize(
        ("model", "expected_columns"),
        [
            (
                Valuation,
                {
                    "id": False,
                    "listing_id": False,
                    "model_version": False,
                    "config_version": False,
                    "cost_assumptions_version": False,
                    "expected_exit_price": True,
                    "exit_price_currency": True,
                    "all_in_acquisition": True,
                    "expected_net_resale": True,
                    "expected_net_profit": True,
                    "roi": True,
                    "low_estimate": True,
                    "high_estimate": True,
                    "confidence": True,
                    "comparable_count": True,
                    "sample_dispersion": True,
                    "adjustment_details": True,
                    "risk_reserve_details": True,
                    "cost_breakdown": True,
                    "created_at": False,
                },
            ),
            (
                DuplicateGroup,
                {
                    "id": False,
                    "model_version": False,
                    "representative_id": False,
                    "method": True,
                    "confidence": True,
                    "created_at": False,
                },
            ),
            (
                DuplicateGroupMember,
                {
                    "id": False,
                    "group_id": False,
                    "listing_id": False,
                    "created_at": False,
                },
            ),
            (
                Opportunity,
                {
                    "id": False,
                    "organization_id": False,
                    "listing_id": False,
                    "valuation_id": False,
                    "material_version": False,
                    "score": True,
                    "state": False,
                    "positive_factors": True,
                    "negative_factors": True,
                    "published_at": True,
                    "state_changed_at": True,
                    "created_at": False,
                },
            ),
            (
                OpportunityView,
                {
                    "id": False,
                    "opportunity_id": False,
                    "user_id": False,
                    "viewed_at": True,
                },
            ),
        ],
    )
    def test_columns_and_nullability_match_migration(self, model, expected_columns):
        columns = model.__table__.c
        assert set(columns.keys()) == set(expected_columns)
        assert {name: columns[name].nullable for name in expected_columns} == expected_columns

    def test_unique_constraints_match_migration(self):
        expected = {
            DuplicateGroupMember: {"uq_duplicate_group_members"},
            Opportunity: {"uq_opportunities_org_listing_version"},
            OpportunityView: {"uq_opportunity_views"},
        }
        for model, names in expected.items():
            assert {
                constraint.name for constraint in model.__table__.constraints if constraint.name
            } >= names

    def test_opportunity_is_tenant_scoped(self):
        assert "organization_id" in Opportunity.__table__.c
        foreign_keys = {
            (foreign_key.parent.name, foreign_key.target_fullname)
            for foreign_key in Opportunity.__table__.foreign_keys
        }
        assert ("organization_id", "organizations.id") in foreign_keys

    async def test_opportunity_foreign_keys_and_unique_constraint(self, session):
        opportunity = await create_opportunity_dependencies(session)
        duplicate = Opportunity(
            id="opp_duplicate",
            organization_id=opportunity.organization_id,
            listing_id=opportunity.listing_id,
            valuation_id=opportunity.valuation_id,
            material_version=opportunity.material_version,
            state="published",
        )
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

    async def test_opportunity_view_foreign_keys_and_uniqueness(self, session):
        opportunity = await create_opportunity_dependencies(session)
        user = await session.get(User, "usr_test")
        assert user is not None
        session.add(
            OpportunityView(
                id="view_test",
                opportunity_id=opportunity.id,
                user_id=user.id,
            )
        )
        await session.commit()

        session.add(
            OpportunityView(
                id="view_duplicate",
                opportunity_id=opportunity.id,
                user_id=user.id,
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()
