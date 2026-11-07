from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import (
    JSON,
    ForeignKey,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class Valuation(ULIDMixin, Base):
    __tablename__ = "valuations"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_valuations"),)

    listing_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("normalized_listings.id", name="fk_valuations_listing_id"),
        nullable=False,
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
    adjustment_details: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    risk_reserve_details: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    cost_breakdown: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
