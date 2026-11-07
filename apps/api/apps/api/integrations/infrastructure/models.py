from __future__ import annotations

from datetime import datetime

from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import ForeignKey, PrimaryKeyConstraint, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class ProviderIntegration(ULIDMixin, Base):
    __tablename__ = "provider_integrations"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_provider_integrations"),
        UniqueConstraint(
            "organization_id",
            "user_id",
            "provider",
            name="uq_provider_integrations_org_user_provider",
        ),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("organizations.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(Text(), ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(Text(), nullable=False)
    external_id_ciphertext: Mapped[str | None] = mapped_column(Text(), nullable=True)
    link_token_hash: Mapped[str | None] = mapped_column(Text(), nullable=True)
    link_expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class PushDevice(ULIDMixin, Base):
    __tablename__ = "push_devices"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_push_devices"),
        UniqueConstraint("token_hash", name="uq_push_devices_token_hash"),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("organizations.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(Text(), ForeignKey("users.id"), nullable=False)
    platform: Mapped[str] = mapped_column(Text(), nullable=False)
    token_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    token_ciphertext: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class PayPalWebhookEvent(Base):
    __tablename__ = "paypal_webhook_events"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_paypal_webhook_events"),)

    id: Mapped[str] = mapped_column(Text(), nullable=False)
    event_type: Mapped[str] = mapped_column(Text(), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
