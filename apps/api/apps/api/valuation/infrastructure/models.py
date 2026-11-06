from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import JSON, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column


class Valuation(ULIDMixin, Base):
    __tablename__ = "valuations"

    listing_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("normalized_listings.id"), nullable=False
    )
    model_version: Mapped[str] = mapped_column(Text(), nullable=False)
    config_version: Mapped[str] = mapped_column(Text(), nullable=False)
    cost_assumptions_version: Mapped[str] = mapped_column(Text(), nullable=False)
    expected_exit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    exit_price_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    all_in_acquisition: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    expected_net_resale: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    expected_net_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    roi: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    low_estimate: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    high_estimate: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    comparable_count: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    sample_dispersion: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    adjustment_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    risk_reserve_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    cost_breakdown: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )


class Opportunity(ULIDMixin, Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "listing_id",
            "material_version",
            name="uq_opportunities_org_listing_version",
        ),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("organizations.id"), nullable=False
    )
    listing_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("normalized_listings.id"), nullable=False
    )
    valuation_id: Mapped[str] = mapped_column(Text(), ForeignKey("valuations.id"), nullable=False)
    material_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    state: Mapped[str] = mapped_column(
        sa.Enum(
            "published",
            "dismissed",
            "contacted",
            "purchased",
            "expired",
            name="opportunity_state",
        ),
        nullable=False,
    )
    positive_factors: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    negative_factors: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    state_changed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )


class OpportunityView(ULIDMixin, Base):
    __tablename__ = "opportunity_views"
    __table_args__ = (UniqueConstraint("opportunity_id", "user_id", name="uq_opportunity_views"),)

    opportunity_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("opportunities.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(Text(), ForeignKey("users.id"), nullable=False)
    viewed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
