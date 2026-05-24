from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.agents.base import AgentsBase

SLUG_PATTERN = r"^[a-z][a-z0-9-]{0,63}$"


class AgentORM(AgentsBase):
    """Persistent agent definition.

    Tenant + slug is the addressable name pair. user_id records the creator
    (audit/ownership). Future tables (agent_versions, documents) will reference
    `id`.
    """

    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_agents_tenant_slug"),
        CheckConstraint(f"slug ~ '{SLUG_PATTERN}'", name="ck_agents_slug_kebab"),
        CheckConstraint("scope IN ('tenant', 'user')", name="ck_agents_scope_valid"),
        Index("ix_agents_tenant_user", "tenant_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4,
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    scope: Mapped[Literal["tenant", "user"]] = mapped_column(
        String(16), nullable=False, server_default="user",
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    documents: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    memory_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
