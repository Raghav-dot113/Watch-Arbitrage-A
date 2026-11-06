from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column


class AuditEvent(ULIDMixin, Base):
    __tablename__ = "audit_events"

    organization_id: Mapped[str | None] = mapped_column(
        Text(), ForeignKey("organizations.id"), nullable=True
    )
    user_id: Mapped[str | None] = mapped_column(Text(), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(Text(), nullable=False)
    resource_type: Mapped[str] = mapped_column(Text(), nullable=False)
    resource_id: Mapped[str] = mapped_column(Text(), nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    trace_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )


class OutboxEvent(ULIDMixin, Base):
    __tablename__ = "outbox_events"

    event_name: Mapped[str] = mapped_column(Text(), nullable=False)
    event_version: Mapped[str] = mapped_column(Text(), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    trace_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(
        sa.Enum("pending", "published", "failed", name="outbox_event_status"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


class FeatureFlag(ULIDMixin, Base):
    __tablename__ = "feature_flags"
    __table_args__ = (UniqueConstraint("key", name="uq_feature_flags_key"),)

    key: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    enabled: Mapped[bool] = mapped_column(
        Boolean(), server_default=sa.text("false"), nullable=False
    )
    organization_ids: Mapped[list[str] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    rollout_pct: Mapped[int] = mapped_column(Integer(), server_default="0", nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False
    )
