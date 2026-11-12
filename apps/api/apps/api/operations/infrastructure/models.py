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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

_outbox_event_status = sa.Enum(
    "pending",
    "published",
    "failed",
    native_enum=False,
).with_variant(
    ENUM(
        "pending",
        "published",
        "failed",
        name="outbox_event_status",
        create_type=True,
    ),
    "postgresql",
)


class AuditEvent(ULIDMixin, Base):
    __tablename__ = "audit_events"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_audit_events"),)

    organization_id: Mapped[str | None] = mapped_column(
        Text(),
        ForeignKey("organizations.id", name="fk_audit_events_organization_id"),
        nullable=True,
    )
    user_id: Mapped[str | None] = mapped_column(
        Text(), ForeignKey("users.id", name="fk_audit_events_user_id"), nullable=True
    )
    action: Mapped[str] = mapped_column(Text(), nullable=False)
    resource_type: Mapped[str] = mapped_column(Text(), nullable=False)
    resource_id: Mapped[str] = mapped_column(Text(), nullable=False)
    details: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    trace_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class OutboxEvent(ULIDMixin, Base):
    __tablename__ = "outbox_events"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_outbox_events"),)

    event_name: Mapped[str] = mapped_column(Text(), nullable=False)
    event_version: Mapped[str] = mapped_column(Text(), nullable=False)
    payload: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    trace_id: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(_outbox_event_status, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


class FeatureFlag(ULIDMixin, Base):
    __tablename__ = "feature_flags"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_feature_flags"),
        UniqueConstraint("key", name="uq_feature_flags_key"),
    )

    key: Mapped[str] = mapped_column(Text(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    enabled: Mapped[bool] = mapped_column(
        Boolean(), server_default=sa.text("false"), nullable=False
    )
    organization_ids: Mapped[list[str] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    rollout_pct: Mapped[int] = mapped_column(Integer(), server_default=sa.text("0"), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
