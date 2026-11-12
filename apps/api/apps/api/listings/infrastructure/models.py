from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import sqlalchemy as sa
from apps.api.duplicates.infrastructure.models import DuplicateGroup, DuplicateGroupMember
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import (
    JSON,
    Date,
    ForeignKey,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

_listing_status = sa.Enum(
    "active",
    "quarantined",
    "suppressed",
    "stale",
    native_enum=False,
).with_variant(
    ENUM(
        "active",
        "quarantined",
        "suppressed",
        "stale",
        name="listing_status",
        create_type=True,
    ),
    "postgresql",
)


class RawSnapshot(ULIDMixin, Base):
    __tablename__ = "raw_snapshots"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_raw_snapshots"),
        UniqueConstraint(
            "source_id",
            "external_id",
            "adapter_version",
            "checksum",
            name="uq_raw_snapshots",
        ),
    )

    source_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("sources.id", name="fk_raw_snapshots_source_id"),
        nullable=False,
    )
    external_id: Mapped[str] = mapped_column(Text(), nullable=False)
    adapter_version: Mapped[str] = mapped_column(Text(), nullable=False)
    checksum: Mapped[str] = mapped_column(Text(), nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    fetched_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )


class ParsedListing(ULIDMixin, Base):
    __tablename__ = "parsed_listings"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_parsed_listings"),
        UniqueConstraint("snapshot_id", name="uq_parsed_listings_snapshot_id"),
    )

    snapshot_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("raw_snapshots.id", name="fk_parsed_listings_snapshot_id"),
        nullable=False,
    )
    parser_version: Mapped[str] = mapped_column(Text(), nullable=False)
    listing_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    price_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    listing_title: Mapped[str | None] = mapped_column(Text(), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    parsed_attributes: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    external_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    listed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class NormalizedListing(ULIDMixin, Base):
    __tablename__ = "normalized_listings"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_normalized_listings"),
        UniqueConstraint(
            "parsed_listing_id",
            name="uq_normalized_listings_parsed_listing_id",
        ),
    )

    parsed_listing_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey(
            "parsed_listings.id",
            name="fk_normalized_listings_parsed_listing_id",
        ),
        nullable=False,
    )
    reference_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("references.id", name="fk_normalized_listings_reference_id"),
        nullable=False,
    )
    normalization_version: Mapped[str] = mapped_column(Text(), nullable=False)
    match_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    match_method: Mapped[str | None] = mapped_column(Text(), nullable=True)
    match_features: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    condition: Mapped[str | None] = mapped_column(Text(), nullable=True)
    set_status: Mapped[str | None] = mapped_column(Text(), nullable=True)
    seller_geography: Mapped[str | None] = mapped_column(Text(), nullable=True)
    normalized_price: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True
    )
    normalized_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    fx_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    fx_source: Mapped[str] = mapped_column(Text(), nullable=False)
    fx_date: Mapped[date] = mapped_column(Date(), nullable=False)
    observation_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(_listing_status, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
