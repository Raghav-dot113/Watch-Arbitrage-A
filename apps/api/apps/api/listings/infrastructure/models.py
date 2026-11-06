from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import JSON, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column


class RawSnapshot(ULIDMixin, Base):
    __tablename__ = "raw_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "external_id",
            "adapter_version",
            "checksum",
            name="uq_raw_snapshots",
        ),
    )

    source_id: Mapped[str] = mapped_column(Text(), ForeignKey("sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(Text(), nullable=False)
    adapter_version: Mapped[str] = mapped_column(Text(), nullable=False)
    checksum: Mapped[str] = mapped_column(Text(), nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    fetched_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


class ParsedListing(ULIDMixin, Base):
    __tablename__ = "parsed_listings"

    snapshot_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("raw_snapshots.id"), nullable=False, unique=True
    )
    parser_version: Mapped[str] = mapped_column(Text(), nullable=False)
    listing_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    price_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    listing_title: Mapped[str | None] = mapped_column(Text(), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    parsed_attributes: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    external_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    listed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )


class NormalizedListing(ULIDMixin, Base):
    __tablename__ = "normalized_listings"

    parsed_listing_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("parsed_listings.id"), nullable=False, unique=True
    )
    reference_id: Mapped[str] = mapped_column(Text(), ForeignKey("references.id"), nullable=False)
    normalization_version: Mapped[str] = mapped_column(Text(), nullable=False)
    match_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    match_method: Mapped[str | None] = mapped_column(Text(), nullable=True)
    match_features: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    condition: Mapped[str | None] = mapped_column(Text(), nullable=True)
    set_status: Mapped[str | None] = mapped_column(Text(), nullable=True)
    seller_geography: Mapped[str | None] = mapped_column(Text(), nullable=True)
    normalized_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    normalized_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    fx_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    fx_source: Mapped[str] = mapped_column(Text(), nullable=False)
    fx_date: Mapped[date] = mapped_column(sa.Date(), nullable=False)
    observation_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Enum("active", "quarantined", "suppressed", "stale", name="listing_status"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )


class DuplicateGroup(ULIDMixin, Base):
    __tablename__ = "duplicate_groups"

    model_version: Mapped[str] = mapped_column(Text(), nullable=False)
    representative_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("normalized_listings.id"), nullable=False
    )
    method: Mapped[str | None] = mapped_column(Text(), nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )


class DuplicateGroupMember(ULIDMixin, Base):
    __tablename__ = "duplicate_group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "listing_id", name="uq_duplicate_group_members"),
    )

    group_id: Mapped[str] = mapped_column(Text(), ForeignKey("duplicate_groups.id"), nullable=False)
    listing_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("normalized_listings.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )
