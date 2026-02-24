from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from echo.context.types import Channel, ContextType
from echo.db.models.context import Context


class ContextTable:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_context(
        self,
        thread_id: UUID,
        opportunity_id: str | None,
        user_id: UUID,
        channel: Channel,
        content: str,
        type: ContextType,
    ) -> UUID:
        context_id = uuid4()
        self.session.add(
            Context(
                context_id=str(context_id),
                thread_id=thread_id,
                opportunity_id=opportunity_id,
                user_id=user_id,
                channel=channel,
                content=content,
                type=type,
            )
        )
        return context_id

    async def update_content(self, context_id: UUID, content: str) -> None:
        result = await self.session.execute(select(Context).where(Context.context_id == str(context_id)))
        row = cast(Context | None, result.scalar_one_or_none())

        if row is None:
            raise ValueError(f"Context {context_id} not found")

        row.content = content

    async def get_context_by_id(self, context_id: UUID) -> Context | None:
        result = await self.session.execute(select(Context).where(Context.context_id == str(context_id)))
        return cast(Context | None, result.scalar_one_or_none())

    async def get_contexts(self) -> list[Context]:
        result = await self.session.execute(select(Context))
        return cast(list[Context], result.scalars().all())

    async def get_context_history(
        self,
        *,
        user_id: UUID | None = None,
        opportunity_id: str | None = None,
        thread_id: UUID | None = None,
        max_age: timedelta = timedelta(days=30),
        types: list[ContextType] | None = None,
        channels: list[Channel] | None = None,
    ) -> list[Context]:
        if thread_id is None and user_id is None and opportunity_id is None:
            raise ValueError("get_context_history requires either thread_id, user_id or opportunity_id")

        if max_age <= timedelta(0):
            raise ValueError("max_age must be a positive timedelta")

        stmt = select(Context).where(Context.added_timestamp >= datetime.now(UTC) - max_age)

        if user_id is not None:
            stmt = stmt.where(Context.user_id == user_id)
        if opportunity_id is not None:
            stmt = stmt.where(Context.opportunity_id == opportunity_id)
        if thread_id is not None:
            stmt = stmt.where(Context.thread_id == thread_id)
        if types:
            stmt = stmt.where(Context.type.in_(types))
        if channels:
            stmt = stmt.where(Context.channel.in_(channels))

        result = await self.session.execute(stmt)
        return cast(list[Context], result.scalars().all())
