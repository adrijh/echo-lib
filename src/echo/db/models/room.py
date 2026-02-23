from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.base import Base


class Room(Base):
    __tablename__ = "rooms"

    room_id: Mapped[str] = mapped_column(String, primary_key=True)
    thread_id: Mapped[UUID] = mapped_column()
    opportunity_id: Mapped[str] = mapped_column()
    start_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_url: Mapped[str | None] = mapped_column()
    metadata_: Mapped[str | None] = mapped_column("metadata", JSON)
