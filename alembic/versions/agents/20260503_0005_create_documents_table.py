"""Create documents table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-03.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column(
            "tenant_id",
            sa.String(length=64),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "user_id",
            sa.String(length=128),
            nullable=False,
            server_default="",
        ),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("filename_normalized", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("blob_key", sa.String(length=1024), nullable=False),
        sa.Column("uploaded_by", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("blob_key", name="uq_documents_blob_key"),
        sa.UniqueConstraint(
            "scope",
            "tenant_id",
            "user_id",
            "filename_normalized",
            name="uq_documents_scope_filename",
        ),
        sa.CheckConstraint(
            "scope IN ('shared', 'tenant', 'user')",
            name="ck_documents_scope_valid",
        ),
        sa.CheckConstraint(
            "(scope = 'shared' AND tenant_id = '' AND user_id = '') "
            "OR (scope = 'tenant' AND tenant_id <> '' AND user_id = '') "
            "OR (scope = 'user' AND user_id <> '' AND tenant_id = '')",
            name="ck_documents_principal_matches_scope",
        ),
    )
    op.create_index(
        "ix_documents_scope_tenant",
        "documents",
        ["scope", "tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_documents_scope_user",
        "documents",
        ["scope", "user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_documents_scope_user", table_name="documents")
    op.drop_index("ix_documents_scope_tenant", table_name="documents")
    op.drop_table("documents")
