from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from apps.api.catalog.infrastructure.models import Brand, Reference, Source
from apps.api.identity.infrastructure import models as _identity_models  # noqa: F401
from apps.api.infrastructure.models import Base
from apps.api.listings.infrastructure.models import (
    NormalizedListing,
    ParsedListing,
    RawSnapshot,
)
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


class TestListingOrmParity:
    @pytest.mark.parametrize(
        ("model", "expected_columns"),
        [
            (
                RawSnapshot,
                {
                    "id": False,
                    "source_id": False,
                    "external_id": False,
                    "adapter_version": False,
                    "checksum": False,
                    "raw_payload": True,
                    "fetched_at": True,
                },
            ),
            (
                ParsedListing,
                {
                    "id": False,
                    "snapshot_id": False,
                    "parser_version": False,
                    "listing_price": True,
                    "price_currency": True,
                    "listing_title": True,
                    "description": True,
                    "parsed_attributes": True,
                    "external_url": True,
                    "listed_at": True,
                    "created_at": False,
                },
            ),
            (
                NormalizedListing,
                {
                    "id": False,
                    "parsed_listing_id": False,
                    "reference_id": False,
                    "normalization_version": False,
                    "match_confidence": True,
                    "match_method": True,
                    "match_features": True,
                    "condition": True,
                    "set_status": True,
                    "seller_geography": True,
                    "normalized_price": True,
                    "normalized_currency": True,
                    "fx_rate": False,
                    "fx_source": False,
                    "fx_date": False,
                    "observation_at": False,
                    "status": False,
                    "created_at": False,
                },
            ),
        ],
    )
    def test_columns_and_nullability_match_migration(self, model, expected_columns):
        columns = model.__table__.c
        assert set(columns.keys()) == set(expected_columns)
        assert {
            name: columns[name].nullable for name in expected_columns
        } == expected_columns

    def test_unique_constraints_match_migration(self):
        expected = {
            RawSnapshot: {"uq_raw_snapshots"},
            ParsedListing: {"uq_parsed_listings_snapshot_id"},
            NormalizedListing: {"uq_normalized_listings_parsed_listing_id"},
        }
        for model, names in expected.items():
            assert {
                constraint.name
                for constraint in model.__table__.constraints
                if constraint.name
            } >= names

    async def test_snapshot_parsed_normalized_chain(self, session):
        brand = Brand(id="brd_test", name="Example", slug="example")
        reference = Reference(id="ref_test", brand_id=brand.id, ref_code="EX-1")
        source = Source(
            id="src_test",
            source_key="example",
            display_name="Example",
            adapter_version="1",
            access_mode="fixture",
        )
        snapshot = RawSnapshot(
            id="raw_test",
            source_id=source.id,
            external_id="listing-1",
            adapter_version="1",
            checksum="abc123",
            raw_payload={"price": "12000.00"},
        )
        parsed = ParsedListing(
            id="parsed_test",
            snapshot_id=snapshot.id,
            parser_version="1",
            listing_price=Decimal("12000.00"),
            price_currency="USD",
        )
        normalized = NormalizedListing(
            id="norm_test",
            parsed_listing_id=parsed.id,
            reference_id=reference.id,
            normalization_version="1",
            normalized_price=Decimal("12000.00"),
            normalized_currency="USD",
            fx_rate=Decimal("1"),
            fx_source="identity",
            fx_date=date(2026, 1, 1),
            observation_at=datetime(2026, 1, 1, tzinfo=UTC),
            status="active",
        )
        session.add_all([brand, reference, source])
        await session.flush()
        session.add(snapshot)
        await session.flush()
        session.add(parsed)
        await session.flush()
        session.add(normalized)
        await session.commit()

        assert await session.get(RawSnapshot, snapshot.id) is not None
        assert await session.get(ParsedListing, parsed.id) is not None
        stored = await session.get(NormalizedListing, normalized.id)
        assert stored is not None
        assert stored.normalized_price == Decimal("12000.00")

    async def test_foreign_keys_are_enforced(self, session):
        invalid = RawSnapshot(
            id="raw_invalid",
            source_id="missing_source",
            external_id="listing-1",
            adapter_version="1",
            checksum="abc123",
        )
        session.add(invalid)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

    async def test_unique_constraints_are_enforced(self, session):
        source = Source(
            id="src_test",
            source_key="example",
            display_name="Example",
            adapter_version="1",
            access_mode="fixture",
        )
        first = RawSnapshot(
            id="raw_1",
            source_id=source.id,
            external_id="listing-1",
            adapter_version="1",
            checksum="abc123",
        )
        duplicate = RawSnapshot(
            id="raw_2",
            source_id=source.id,
            external_id="listing-1",
            adapter_version="1",
            checksum="abc123",
        )
        session.add_all([source, first, duplicate])
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()
