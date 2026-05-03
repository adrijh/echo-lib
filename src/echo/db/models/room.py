from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.base import Base


class Room(Base):
    __tablename__ = "rooms"

    room_id: Mapped[str] = mapped_column(String, primary_key=True)
    thread_id: Mapped[UUID | None] = mapped_column()
    opportunity_id: Mapped[str | None] = mapped_column(index=True)
    start_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    report_url: Mapped[str | None] = mapped_column()
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)
    timeline: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_rooms_start_timestamp",
            "start_timestamp",
            postgresql_where=text("start_timestamp IS NOT NULL"),
        ),
    )
