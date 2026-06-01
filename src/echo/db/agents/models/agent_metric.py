from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Identity,
    Index,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.agents.base import AgentsBase


class AgentMetricORM(AgentsBase):
    """Append-only analytics fact table.

    One row per measurement, pivoted by ``metric`` (e.g. ``message.received``,
    ``tool.call``). Written by the consumer draining the metrics queue.

    Deliberately has no foreign key to ``agents``: analytics should survive
    agent deletion, and a fact table written at high volume should not pay
    referential-integrity costs. ``agent_id`` is a plain indexed key.
    """

    __tablename__ = "agent_metrics"
    __table_args__ = (
        CheckConstraint(
            "source IN ('system', 'track', 'inferred')",
            name="ck_agent_metrics_source_valid",
        ),
        Index(
            "ix_agent_metrics_lookup",
            "tenant_id",
            "agent_id",
            "metric",
            "occurred_at",
        ),
        Index(
            "uq_agent_metrics_dedup_key",
            "dedup_key",
            unique=True,
            postgresql_where=text("dedup_key IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    run_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    thread_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    metric: Mapped[str] = mapped_column(String(128), nullable=False)
    value_num: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    value_str: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dimensions: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    source: Mapped[Literal["system", "track", "inferred"]] = mapped_column(String(16), nullable=False)
    dedup_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
