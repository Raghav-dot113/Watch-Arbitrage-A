"""Add PayPal subscription tracking and webhook receipts.

Revision ID: c9a6d6a64c10
Revises: b13d4c92e801
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c9a6d6a64c10"
down_revision: str | None = "b13d4c92e801"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("paypal_payer_id", sa.Text(), nullable=True))
    op.add_column("subscriptions", sa.Column("paypal_subscription_id", sa.Text(), nullable=True))
    op.add_column("subscriptions", sa.Column("paypal_approval_url", sa.Text(), nullable=True))
    op.add_column(
        "subscriptions",
        sa.Column("paypal_updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index(
        "uq_subscriptions_paypal_subscription_id",
        "subscriptions",
        ["paypal_subscription_id"],
        unique=True,
    )
    op.create_table(
        "paypal_webhook_events",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column(
            "received_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_paypal_webhook_events"),
    )


def downgrade() -> None:
    op.drop_table("paypal_webhook_events")
    op.drop_index(
        "uq_subscriptions_paypal_subscription_id",
        table_name="subscriptions",
    )
    op.drop_column("subscriptions", "paypal_updated_at")
    op.drop_column("subscriptions", "paypal_approval_url")
    op.drop_column("subscriptions", "paypal_subscription_id")
    op.drop_column("subscriptions", "paypal_payer_id")
