import json
from datetime import timedelta
from typing import Self
from uuid import UUID, uuid4

from echo.context.types import BlobUrl, Chat
from echo.store.context import ContextRow
from echo.store.store import Store
from echo.store.users import UserRow


class UserContext:
    def __init__(
        self,
        store: Store,
        thread_id: UUID,
        user_data: UserRow,
        channel: str,
    ) -> None:
        self.store = store
        self.thread_id = thread_id
        self.user_data = user_data
        self.channel = channel

    @classmethod
    def from_opportunity_id(
        cls,
        store: Store,
        opportunity_id: str,
        channel: str,
        thread_id: UUID | None = None,
    ) -> Self:
        user_data = store.users.get_user(opportunity_id=opportunity_id)

        if not user_data:
            raise RuntimeError(
                f"Could not find user with opportunity_id: {opportunity_id}"
            )

        if not thread_id:
            thread_id = uuid4()

        return cls(
            store=store,
            user_data=user_data,
            channel=channel,
            thread_id=thread_id,
        )

    def get_context(
        self,
        *,
        max_age: timedelta = timedelta(days=30),
        types: list[str] | None = None,
        channels: list[str] | None = None,
    ) -> list[ContextRow]:
        return self.store.context.get_context_history(
            opportunity_id=self.user_data.opportunity_id,
            max_age=max_age,
            types=types,
            channels=channels,
        )

    def add_summary(self, summary: BlobUrl) -> None:
        content = json.dumps(summary)

        self.store.context.create_context(
            thread_id=self.thread_id,
            opportunity_id=self.user_data.opportunity_id,
            user_id=self.user_data.user_id,
            channel=self.channel,
            type="summary",
            content=content,
        )

    def add_chat(self, chat: Chat) -> None:
        content = json.dumps(chat)

        self.store.context.create_context(
            thread_id=self.thread_id,
            opportunity_id=self.user_data.opportunity_id,
            user_id=self.user_data.user_id,
            channel=self.channel,
            type="chat",
            content=content,
        )
