from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import (
    ForeignKey,
    Numeric,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class DuplicateGroup(ULIDMixin, Base):
    __tablename__ = "duplicate_groups"
    __table_args__ = (PrimaryKeyConstraint("id", name="pk_duplicate_groups"),)

    model_version: Mapped[str] = mapped_column(Text(), nullable=False)
    representative_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey(
            "normalized_listings.id",
            name="fk_duplicate_groups_representative_id",
        ),
        nullable=False,
    )
    method: Mapped[str | None] = mapped_column(Text(), nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class DuplicateGroupMember(ULIDMixin, Base):
    __tablename__ = "duplicate_group_members"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_duplicate_group_members"),
        UniqueConstraint("group_id", "listing_id", name="uq_duplicate_group_members"),
    )

    group_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("duplicate_groups.id", name="fk_duplicate_group_members_group_id"),
        nullable=False,
    )
    listing_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey(
            "normalized_listings.id",
            name="fk_duplicate_group_members_listing_id",
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
