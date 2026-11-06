from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column


class Feedback(ULIDMixin, Base):
    __tablename__ = "feedbacks"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_feedbacks_idempotency_key"),)

    organization_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("organizations.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(Text(), ForeignKey("users.id"), nullable=False)
    opportunity_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("opportunities.id"), nullable=False
    )
    decision: Mapped[str] = mapped_column(
        sa.Enum("purchased", "contacted", "dismissed", name="feedback_decision"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )


class TradeOutcome(ULIDMixin, Base):
    __tablename__ = "trade_outcomes"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_trade_outcomes_idempotency_key"),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("organizations.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(Text(), ForeignKey("users.id"), nullable=False)
    opportunity_id: Mapped[str | None] = mapped_column(
        Text(), ForeignKey("opportunities.id"), nullable=True
    )
    reference_id: Mapped[str] = mapped_column(Text(), ForeignKey("references.id"), nullable=False)
    acquisition_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    acquisition_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    resale_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    resale_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    actual_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    days_to_sell: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )
