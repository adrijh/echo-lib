import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.dialects.postgresql import (
    ARRAY,
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.agents.base import AgentsBase


class RoleORM(AgentsBase):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    permissions: Mapped[list[str]] = mapped_column(
        ARRAY(String(128)), nullable=False, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


membership_roles = Table(
    "membership_roles",
    AgentsBase.metadata,
    Column(
        "membership_id",
        PGUUID(as_uuid=True),
        ForeignKey("tenant_memberships.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
