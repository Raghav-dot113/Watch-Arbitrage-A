"""Provider connections and idempotent Stripe webhook receipts.

Revision ID: b13d4c92e801
Revises: f2b39ba97b17
Create Date: 2026-11-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b13d4c92e801"
down_revision: str | None = "f2b39ba97b17"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_integrations",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("organization_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("external_id_ciphertext", sa.Text(), nullable=True),
        sa.Column("link_token_hash", sa.Text(), nullable=True),
        sa.Column("link_expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_provider_integrations"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_provider_integrations_organization_id",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_provider_integrations_user_id"),
        sa.UniqueConstraint(
            "organization_id",
            "user_id",
            "provider",
            name="uq_provider_integrations_org_user_provider",
        ),
    )
    op.create_index(
        "idx_provider_integrations_org_user",
        "provider_integrations",
        ["organization_id", "user_id"],
    )

    op.create_table(
        "push_devices",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("organization_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("token_ciphertext", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_push_devices"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], name="fk_push_devices_organization_id"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_push_devices_user_id"),
        sa.UniqueConstraint("token_hash", name="uq_push_devices_token_hash"),
    )
    op.create_index(
        "idx_push_devices_org_user",
        "push_devices",
        ["organization_id", "user_id"],
    )

    op.create_table(
        "stripe_webhook_events",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column(
            "received_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_stripe_webhook_events"),
    )


def downgrade() -> None:
    op.drop_table("stripe_webhook_events")
    op.drop_index("idx_push_devices_org_user", table_name="push_devices")
    op.drop_table("push_devices")
    op.drop_index("idx_provider_integrations_org_user", table_name="provider_integrations")
    op.drop_table("provider_integrations")
