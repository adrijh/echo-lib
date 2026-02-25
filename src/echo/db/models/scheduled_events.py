import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    UUID,
    DateTime,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.base import Base


class ScheduledEvent(Base):
    __tablename__ = "scheduled_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[str | None] = mapped_column(JSON, nullable=False)
    metadata_: Mapped[str | None] = mapped_column("metadata", JSON)
    status: Mapped[str] = mapped_column(Text)
    added_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
