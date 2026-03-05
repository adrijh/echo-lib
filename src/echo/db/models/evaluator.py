import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    UUID,
    DateTime,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.base import Base


class Evaluator(Base):
    __tablename__ = "evaluators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    spec: Mapped[dict[str, Any] | list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    added_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
