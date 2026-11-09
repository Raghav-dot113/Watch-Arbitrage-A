from __future__ import annotations

from datetime import datetime
from typing import Any

from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import JSON, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column


class IdempotencyRecord(ULIDMixin, Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "route_key",
            "idempotency_key",
            name="uq_idempotency_records_scope",
        ),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("organizations.id"), nullable=False
    )
    route_key: Mapped[str] = mapped_column(Text(), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(Text(), nullable=False)
    request_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer(), nullable=False)
    response_body: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
