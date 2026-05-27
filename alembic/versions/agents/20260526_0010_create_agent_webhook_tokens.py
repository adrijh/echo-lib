"""Create agent_webhook_tokens table.

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-26.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_webhook_tokens",
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("token_prefix", sa.String(length=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_agent_webhook_tokens_agent_id",
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("agent_webhook_tokens")
