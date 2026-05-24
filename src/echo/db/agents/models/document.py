from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.agents.base import AgentsBase


class DocumentORM(AgentsBase):
    """Persistent reference to a document blob in object storage.

    Documents are agent context files uploaded by users and scoped at one of
    three layers: shared (global), tenant (team), or user (private). The blob
    lives in MINIO_BUCKET_DOCUMENTS at ``blob_key``; this row is the metadata
    authority — listings and uniqueness checks go through Postgres rather
    than scanning S3.

    ``tenant_id`` and ``user_id`` are stored as empty strings rather than
    NULL when not applicable: Postgres unique constraints treat NULL values
    as distinct by default, which would silently allow duplicate
    shared/tenant rows. Empty strings give us the uniqueness we want without
    relying on the NULLS NOT DISTINCT clause (Postgres 15+).
    """

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint(
            "scope",
            "tenant_id",
            "user_id",
            "filename_normalized",
            name="uq_documents_scope_filename",
        ),
        CheckConstraint(
            "scope IN ('shared', 'tenant', 'user')",
            name="ck_documents_scope_valid",
        ),
        CheckConstraint(
            "(scope = 'shared' AND tenant_id = '' AND user_id = '') "
            "OR (scope = 'tenant' AND tenant_id <> '' AND user_id = '') "
            "OR (scope = 'user' AND user_id <> '' AND tenant_id = '')",
            name="ck_documents_principal_matches_scope",
        ),
        Index("ix_documents_scope_tenant", "scope", "tenant_id"),
        Index("ix_documents_scope_user", "scope", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4,
    )
    scope: Mapped[Literal["shared", "tenant", "user"]] = mapped_column(
        String(16), nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default="",
    )
    user_id: Mapped[str] = mapped_column(
        String(128), nullable=False, server_default="",
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    filename_normalized: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    blob_key: Mapped[str] = mapped_column(
        String(1024), nullable=False, unique=True,
    )
    uploaded_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


def normalize_filename(filename: str) -> str:
    """Canonical form for collision detection.

    Trims whitespace and lowercases. Original casing is preserved in the
    `filename` column for display; this column is for the unique constraint.
    """
    return filename.strip().lower()
