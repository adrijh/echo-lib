import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from echo.db.base import Base

if TYPE_CHECKING:
    from echo.db.models.campaign_detail import CampaignDetail


class CampaignStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    market: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus),
        default=CampaignStatus.DRAFT,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    total_users: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    completed_users: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    users: Mapped[list["CampaignDetail"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
