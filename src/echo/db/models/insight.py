import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    UUID,
    DateTime,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.base import Base


class CallRecord(Base):
    __tablename__ = "call_history_details"

    insight_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    campaign_id: Mapped[str | None] = mapped_column(Text)
    room_id: Mapped[str | None] = mapped_column(Text)
    opportunity_id: Mapped[str | None] = mapped_column(Text)
    thread_id: Mapped[uuid.UUID | None] = mapped_column(UUID)

    user_name: Mapped[str | None] = mapped_column(Text)
    user_phone: Mapped[str | None] = mapped_column(Text)
    user_email: Mapped[str | None] = mapped_column(Text)

    plancode: Mapped[str | None] = mapped_column(Text)
    market: Mapped[str | None] = mapped_column(Text)

    answer: Mapped[bool | None] = mapped_column()
    voicemail_answer: Mapped[bool | None] = mapped_column()

    availability: Mapped[str | None] = mapped_column(Text)
    recording_consent: Mapped[bool | None] = mapped_column()

    motivation: Mapped[str | None] = mapped_column(Text)
    work_status: Mapped[str | None] = mapped_column(Text)

    financial_interest: Mapped[bool | None] = mapped_column()
    financial_topics: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    financial_details: Mapped[str | None] = mapped_column(Text)

    objection: Mapped[str | None] = mapped_column(Text)
    score: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)

    callback_requested: Mapped[bool | None] = mapped_column()
    callback_reference_day: Mapped[str | None] = mapped_column(Text)
    callback_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    duration_seconds: Mapped[int | None] = mapped_column()
    recording_url: Mapped[str | None] = mapped_column(Text)

    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
