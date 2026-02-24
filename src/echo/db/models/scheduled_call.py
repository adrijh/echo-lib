from datetime import datetime

from sqlalchemy import (
    DateTime,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.base import Base


class ScheduledCall(Base):
    __tablename__ = "schedule_calls"

    opportunity_id: Mapped[str] = mapped_column(Text, primary_key=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[str | None] = mapped_column("metadata", JSONB)
    status: Mapped[str] = mapped_column(Text)
    added_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
