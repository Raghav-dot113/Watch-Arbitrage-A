from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column


class AlertRule(ULIDMixin, Base):
    __tablename__ = "alert_rules"

    organization_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("organizations.id"), nullable=False
    )
    created_by: Mapped[str] = mapped_column(Text(), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    filters: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    channels: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    cooldown_minutes: Mapped[int] = mapped_column(Integer(), server_default="60", nullable=False)
    is_enabled: Mapped[bool] = mapped_column(
        Boolean(), server_default=sa.text("true"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )


class AlertDelivery(ULIDMixin, Base):
    __tablename__ = "alert_deliveries"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_alert_deliveries_idempotency_key"),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("organizations.id"), nullable=False
    )
    rule_id: Mapped[str] = mapped_column(Text(), ForeignKey("alert_rules.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(Text(), ForeignKey("users.id"), nullable=False)
    opportunity_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("opportunities.id"), nullable=False
    )
    material_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    channel: Mapped[str] = mapped_column(Text(), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(Text(), nullable=False)
    delivery_status: Mapped[str] = mapped_column(
        sa.Enum("pending", "sent", "failed", "suppressed", name="delivery_status"),
        nullable=False,
    )
    provider_message_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )
