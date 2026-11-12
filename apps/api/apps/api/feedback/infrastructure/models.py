from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

_feedback_decision = sa.Enum(
    "purchased",
    "contacted",
    "dismissed",
    native_enum=False,
).with_variant(
    ENUM(
        "purchased",
        "contacted",
        "dismissed",
        name="feedback_decision",
        create_type=True,
    ),
    "postgresql",
)


class Feedback(ULIDMixin, Base):
    __tablename__ = "feedbacks"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_feedbacks"),
        UniqueConstraint("idempotency_key", name="uq_feedbacks_idempotency_key"),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("organizations.id", name="fk_feedbacks_organization_id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("users.id", name="fk_feedbacks_user_id"), nullable=False
    )
    opportunity_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("opportunities.id", name="fk_feedbacks_opportunity_id"),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(_feedback_decision, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class TradeOutcome(ULIDMixin, Base):
    __tablename__ = "trade_outcomes"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_trade_outcomes"),
        UniqueConstraint("idempotency_key", name="uq_trade_outcomes_idempotency_key"),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("organizations.id", name="fk_trade_outcomes_organization_id"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("users.id", name="fk_trade_outcomes_user_id"), nullable=False
    )
    opportunity_id: Mapped[str | None] = mapped_column(
        Text(),
        ForeignKey("opportunities.id", name="fk_trade_outcomes_opportunity_id"),
        nullable=True,
    )
    reference_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("references.id", name="fk_trade_outcomes_reference_id"), nullable=False
    )
    acquisition_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    acquisition_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    resale_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    resale_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    actual_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    days_to_sell: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
