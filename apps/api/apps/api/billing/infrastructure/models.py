from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column


class Subscription(ULIDMixin, Base):
    __tablename__ = "subscriptions"

    organization_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("organizations.id"), nullable=False
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(
        sa.Enum("trialing", "active", "past_due", "canceled", "unpaid", name="subscription_status"),
        nullable=False,
    )
    plan_id: Mapped[str | None] = mapped_column(String(), nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    trial_end: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )


class StripeWebhookEvent(ULIDMixin, Base):
    __tablename__ = "stripe_webhook_events"

    provider_event_id: Mapped[str] = mapped_column(Text(), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(Text(), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )
