from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Index,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.base import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        Index("idx_users_opportunity_id", "opportunity_id"),
        Index("idx_users_user_id", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column()
    contact_id: Mapped[str | None] = mapped_column()
    opportunity_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str | None] = mapped_column()
    last_name: Mapped[str | None] = mapped_column()
    phone_number: Mapped[str | None] = mapped_column()
    mail: Mapped[str | None] = mapped_column()
    market: Mapped[str | None] = mapped_column()
    faculty: Mapped[str | None] = mapped_column()
    plancode: Mapped[str | None] = mapped_column()
    track: Mapped[str | None] = mapped_column()
    is_active: Mapped[bool] = mapped_column(server_default="true")
    added_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
