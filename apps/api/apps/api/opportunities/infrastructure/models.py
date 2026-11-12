from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from apps.api.infrastructure.models import Base, ULIDMixin
from sqlalchemy import (
    JSON,
    ForeignKey,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

_opportunity_state = sa.Enum(
    "published",
    "dismissed",
    "contacted",
    "purchased",
    "expired",
    native_enum=False,
).with_variant(
    ENUM(
        "published",
        "dismissed",
        "contacted",
        "purchased",
        "expired",
        name="opportunity_state",
        create_type=True,
    ),
    "postgresql",
)


class Opportunity(ULIDMixin, Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_opportunities"),
        UniqueConstraint(
            "organization_id",
            "listing_id",
            "material_version",
            name="uq_opportunities_org_listing_version",
        ),
    )

    organization_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("organizations.id", name="fk_opportunities_organization_id"),
        nullable=False,
    )
    listing_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey("normalized_listings.id", name="fk_opportunities_listing_id"),
        nullable=False,
    )
    valuation_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("valuations.id", name="fk_opportunities_valuation_id"), nullable=False
    )
    material_version: Mapped[int] = mapped_column(Integer(), nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    state: Mapped[str] = mapped_column(_opportunity_state, nullable=False)
    positive_factors: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    negative_factors: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    state_changed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )


class OpportunityView(ULIDMixin, Base):
    __tablename__ = "opportunity_views"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_opportunity_views"),
        UniqueConstraint("opportunity_id", "user_id", name="uq_opportunity_views"),
    )

    opportunity_id: Mapped[str] = mapped_column(
        Text(),
        ForeignKey(
            "opportunities.id",
            name="fk_opportunity_views_opportunity_id",
        ),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        Text(), ForeignKey("users.id", name="fk_opportunity_views_user_id"), nullable=False
    )
    viewed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
