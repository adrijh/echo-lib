import enum
import uuid
from typing import TYPE_CHECKING, TypedDict

from sqlalchemy import Enum, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from echo.db.base import Base

if TYPE_CHECKING:
    from echo.db.models.campaign import Campaign
    from echo.db.models.user import User


class CampaignUserStatus(enum.Enum):
    PENDING = "pending"
    RETRY = "retry"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AttemptData(TypedDict):
    called_at: str | None
    next_call_after: str | None


class CampaignDetail(Base):
    __tablename__ = "campaign_details"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id"),
        nullable=False,
    )

    opportunity_id: Mapped[int] = mapped_column(
        ForeignKey("users.opportunity_id"),
        nullable=False,
    )

    status: Mapped[CampaignUserStatus] = mapped_column(
        Enum(CampaignUserStatus),
        default=CampaignUserStatus.PENDING,
        nullable=False,
    )

    market: Mapped[str] = mapped_column(nullable=False)

    plancode: Mapped[str] = mapped_column(nullable=False)

    attempts: Mapped[list[AttemptData]] = mapped_column(
        MutableList.as_mutable(JSON),
        default=list,
        nullable=False,
    )

    campaign: Mapped["Campaign"] = relationship(back_populates="users")

    user: Mapped["User"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "opportunity_id",
            name="uq_campaign_opportunity",
        ),
        Index("ix_campaign_status", "campaign_id", "status"),
    )
