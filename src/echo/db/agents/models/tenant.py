import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from echo.db.agents.base import AgentsBase
from echo.db.agents.models.agent import SLUG_PATTERN
from echo.db.agents.models.role import membership_roles

if TYPE_CHECKING:
    from echo.db.agents.models.role import RoleORM
    from echo.db.agents.models.user import UserORM


class TenantORM(AgentsBase):
    __tablename__ = "tenants"
    __table_args__ = (CheckConstraint(f"slug ~ '{SLUG_PATTERN}'", name="ck_tenants_slug_kebab"),)

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    memberships: Mapped[list["TenantMembershipORM"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class TenantMembershipORM(AgentsBase):
    __tablename__ = "tenant_memberships"
    __table_args__ = (UniqueConstraint("user_id", "tenant_id", name="uq_membership_user_tenant"),)

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["UserORM"] = relationship(back_populates="memberships")
    tenant: Mapped[TenantORM] = relationship(back_populates="memberships")
    roles: Mapped[list["RoleORM"]] = relationship(secondary=membership_roles, lazy="selectin")

    @property
    def permissions(self) -> set[str]:
        return {p for r in self.roles for p in r.permissions}
