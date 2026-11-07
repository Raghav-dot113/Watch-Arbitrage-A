from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import (
    JSON,
    Boolean,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

_delivery_status = sa.Enum(
    "pending",
    "sent",
    "failed",
    "suppressed",
    native_enum=False,
).with_variant(
    ENUM(
        "pending",
        "sent",
        "failed",
        "suppressed",
        name="delivery_status",
        create_type=False,
    ),
    "postgresql",
)


class AlertRule(ULIDMixin, Base):
    __tablename__ = "alert_rules"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_alert_rules"),)

    organization_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("organizations.id", name="fk_alert_rules_organization_id"),
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(
        Text(), ForeignKey("users.id", name="fk_alert_rules_created_by"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text(), nullable=False)
    filters: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    channels: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    cooldown_minutes: Mapped[int] = mapped_column(
        Integer(), server_default=sa.text("60"), nullable=False
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean(), server_default=sa.text("true"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class AlertDelivery(ULIDMixin, Base):
    __tablename__ = "alert_deliveries"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_alert_deliveries"),
        sa.UniqueConstraint("idempotency_key", name="uq_alert_deliveries_idempotency_key"),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("organizations.id", name="fk_alert_deliveries_organization_id"),
        nullable=False,
    )
    rule_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("alert_rules.id", name="fk_alert_deliveries_rule_id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("users.id", name="fk_alert_deliveries_user_id"), nullable=False
    )
    opportunity_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("opportunities.id", name="fk_alert_deliveries_opportunity_id"),
        nullable=False,
    )
    material_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    channel: Mapped[str] = mapped_column(Text(), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(Text(), nullable=False)
    delivery_status: Mapped[str] = mapped_column(_delivery_status, nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
