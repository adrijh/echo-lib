"""Create agent_metrics table.

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-01.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_metrics",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metric", sa.String(length=128), nullable=False),
        sa.Column("value_num", sa.Numeric(), nullable=True),
        sa.Column("value_str", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column(
            "dimensions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("dedup_key", sa.Text(), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "source IN ('system', 'track', 'inferred')",
            name="ck_agent_metrics_source_valid",
        ),
    )
    op.create_index(
        "ix_agent_metrics_lookup",
        "agent_metrics",
        ["tenant_id", "agent_id", "metric", "occurred_at"],
    )
    op.create_index(
        "uq_agent_metrics_dedup_key",
        "agent_metrics",
        ["dedup_key"],
        unique=True,
        postgresql_where=sa.text("dedup_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_agent_metrics_dedup_key", table_name="agent_metrics")
    op.drop_index("ix_agent_metrics_lookup", table_name="agent_metrics")
    op.drop_table("agent_metrics")
