from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from apps.api.billing.domain import SubscriptionStatus
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint, Text
from sqlalchemy.dialects.postgresql import ENUM, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

_subscription_status = sa.Enum(
    "trialing",
    "active",
    "past_due",
    "canceled",
    "unpaid",
    native_enum=False,
).with_variant(
    ENUM(
        "trialing",
        "active",
        "past_due",
        "canceled",
        "unpaid",
        name="subscription_status",
        create_type=True,
    ),
    "postgresql",
)


class Subscription(ULIDMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_subscriptions"),
        Index(
            "uq_subscriptions_paypal_subscription_id",
            "paypal_subscription_id",
            unique=True,
        ),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("organizations.id", name="fk_subscriptions_organization_id"),
        nullable=False,
    )
    paypal_payer_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    paypal_subscription_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    paypal_approval_url: Mapped[str | None] = mapped_column(Text(), nullable=True)
    paypal_updated_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    status: Mapped[SubscriptionStatus] = mapped_column(_subscription_status, nullable=False)
    plan_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    trial_end: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
