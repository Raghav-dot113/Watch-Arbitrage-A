"""Add durable Stripe webhook replay protection.

Revision ID: f3c8d2a1b6e4
Revises: f2b39ba97b17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f3c8d2a1b6e4"
down_revision: str | None = "f2b39ba97b17"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stripe_webhook_events",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("provider_event_id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column(
            "received_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_stripe_webhook_events"),
        sa.UniqueConstraint(
            "provider_event_id",
            name="uq_stripe_webhook_events_provider_event_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("stripe_webhook_events")
