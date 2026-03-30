from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from echo.db.base import Base
from echo.db.models.room import Room


class AdversaryStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    STOPPED = "stopped"


class AdversaryMode(enum.Enum):
    ADVERSARY = "adversary"
    CHAT = "chat"


class Adversary(Base):
    __tablename__ = "adversary"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    mode: Mapped[AdversaryMode] = mapped_column(Enum(AdversaryMode), nullable=False)
    status: Mapped[AdversaryStatus] = mapped_column(
        Enum(AdversaryStatus),
        default=AdversaryStatus.STOPPED,
        nullable=False,
    )
    max_turns: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)
    messages: Mapped[list[dict[str, Any]]] = mapped_column(
        MutableList.as_mutable(JSONB),
        default=list,
        server_default=text("'[]'::jsonb"),
        nullable=False,
    )
    session_id: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    details: Mapped[list[AdversaryDetail]] = relationship(
        back_populates="adversary",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AdversaryDetailStatus(enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class AdversaryDetail(Base):
    __tablename__ = "adversary_detail"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    adversary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("adversary.id", ondelete="CASCADE"),
        nullable=False,
    )
    room_name: Mapped[str] = mapped_column(
        String,
        ForeignKey("rooms.room_id"),
        nullable=False,
    )
    status: Mapped[AdversaryDetailStatus] = mapped_column(
        Enum(AdversaryDetailStatus),
        default=AdversaryDetailStatus.RUNNING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    adversary: Mapped[Adversary] = relationship(back_populates="details")
    room: Mapped[Room] = relationship(lazy="joined")
