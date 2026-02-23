from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.base import Base

type JsonType = dict[str, Any] | list[dict[str, Any]]


class Context(Base):
    __tablename__ = "context"

    context_id: Mapped[str] = mapped_column(String, primary_key=True)
    thread_id: Mapped[UUID] = mapped_column()
    opportunity_id: Mapped[str] = mapped_column()
    user_id: Mapped[UUID] = mapped_column()
    content: Mapped[str] = mapped_column(JSON)
    type: Mapped[str] = mapped_column()
    channel: Mapped[str] = mapped_column()
    added_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
