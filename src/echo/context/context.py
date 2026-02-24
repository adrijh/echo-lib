import json
from datetime import timedelta
from types import TracebackType
from typing import Self
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from echo.context.types import BlobUrl, Channel, Chat, ContextType
from echo.db.base import get_sessionmaker
from echo.db.models.context import Context
from echo.db.models.user import User
from echo.store.store import PostgresStore


class UserContext:
    def __init__(
        self,
        opportunity_id: str,
        channel: Channel,
        thread_id: UUID | None = None,
    ) -> None:
        self.opportunity_id = opportunity_id
        self.channel: Channel = channel
        self.thread_id = thread_id or uuid4()

        self._session: AsyncSession | None = None
        self._store: PostgresStore | None = None
        self._user: User | None = None

    @property
    def store(self) -> PostgresStore:
        if self._store is None:
            raise RuntimeError("UserContext is not open.")
        return self._store

    @property
    def user(self) -> User:
        if self._user is None:
            raise RuntimeError("UserContext is not open.")
        return self._user

    async def __aenter__(self) -> Self:
        sessionmaker = get_sessionmaker()
        self._session = sessionmaker()

        if not self._session:
            raise RuntimeError("Could not initiate database session")

        self._store = PostgresStore(self._session)

        self._user = await self._store.users.get_user(opportunity_id=self.opportunity_id)

        if self._user is None:
            raise RuntimeError("User not found")

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        session = self._session
        if session is None:
            return

        try:
            if exc_type is None:
                await session.commit()
            else:
                await session.rollback()
        finally:
            await session.close()
            self._session = None
            self._store = None
            self._user = None

    async def get_context(
        self,
        *,
        max_age: timedelta = timedelta(days=30),
        types: list[ContextType] | None = None,
        channels: list[Channel] | None = None,
    ) -> list[Context]:
        return await self.store.context.get_context_history(
            opportunity_id=self.user.opportunity_id,
            max_age=max_age,
            types=types,
            channels=channels,
        )

    async def add_blob(self, blob: BlobUrl) -> None:
        await self.store.context.create_context(
            thread_id=self.thread_id,
            opportunity_id=self.user.opportunity_id,
            user_id=self.user.user_id,
            channel=self.channel,
            type="blob",
            content=json.dumps(blob),
        )

    async def add_chat(self, chat: Chat) -> None:
        await self.store.context.create_context(
            thread_id=self.thread_id,
            opportunity_id=self.user.opportunity_id,
            user_id=self.user.user_id,
            channel=self.channel,
            type="chat",
            content=json.dumps(chat),
        )

    async def add_summary(self, summary: str) -> None:
        await self.store.context.create_context(
            thread_id=self.thread_id,
            opportunity_id=self.user.opportunity_id,
            user_id=self.user.user_id,
            channel=self.channel,
            type="summary",
            content=json.dumps(
                {"summary": summary},
                ensure_ascii=False,
            ),
        )
