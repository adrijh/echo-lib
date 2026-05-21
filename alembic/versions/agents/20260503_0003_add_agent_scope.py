"""Add scope column to agents table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-03.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "scope",
            sa.String(length=16),
            nullable=False,
            server_default="user",
        ),
    )
    op.create_check_constraint(
        "ck_agents_scope_valid",
        "agents",
        "scope IN ('tenant', 'user')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_agents_scope_valid", "agents", type_="check")
    op.drop_column("agents", "scope")
