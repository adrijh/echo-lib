from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from echo.db.agents.base import AgentsBase


class AgentWebhookTokenORM(AgentsBase):
    """Bearer token used by external systems to invoke a specific agent.

    One row per agent (agent_id is PK). Rotating the token replaces the row;
    revoking deletes it. Cascade-delete from agents keeps stale rows out.

    Only the bcrypt hash of the secret is stored; ``token_prefix`` keeps the
    first few characters so the UI can show "whk_a1b2..." without holding the
    full token.
    """

    __tablename__ = "agent_webhook_tokens"

    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    token_prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
