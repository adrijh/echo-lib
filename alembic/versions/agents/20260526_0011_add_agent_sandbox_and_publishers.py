"""Add sandbox_enabled and publishers columns to agents table.

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-26.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "sandbox_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "agents",
        sa.Column(
            "publishers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("""'["rabbitmq", "redis"]'::jsonb"""),
        ),
    )


def downgrade() -> None:
    op.drop_column("agents", "publishers")
    op.drop_column("agents", "sandbox_enabled")
