import json
from datetime import timedelta
from typing import Self
from uuid import UUID, uuid4

from langfuse.langchain import CallbackHandler

from echo.context.chain import build_chain
from echo.context.types import BlobUrl, Channel, Chat, ContextType
from echo.store.context import ContextRow
from echo.store.store import Store
from echo.store.users import UserRow
from echo.utils.storage import get_blob_content


class UserContext:
    def __init__(
        self,
        store: Store,
        thread_id: UUID,
        user_data: UserRow,
        channel: Channel,
    ) -> None:
        self.store = store
        self.thread_id = thread_id
        self.user_data = user_data
        self.channel: Channel = channel

    @classmethod
    def from_opportunity_id(
        cls,
        store: Store,
        opportunity_id: str,
        channel: Channel,
        thread_id: UUID | None = None,
    ) -> Self:
        user_data = store.users.get_user(opportunity_id=opportunity_id)

        if not user_data:
            raise RuntimeError(f"Could not find user with opportunity_id: {opportunity_id}")

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
        types: list[ContextType] | None = None,
        channels: list[Channel] | None = None,
    ) -> list[ContextRow]:
        return self.store.context.get_context_history(
            opportunity_id=self.user_data.opportunity_id,
            max_age=max_age,
            types=types,
            channels=channels,
        )

    def add_blob(self, blob: BlobUrl) -> None:
        content = json.dumps(blob)

        self.store.context.create_context(
            thread_id=self.thread_id,
            opportunity_id=self.user_data.opportunity_id,
            user_id=self.user_data.user_id,
            channel=self.channel,
            type="blob",
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

    async def add_summarize(self, blob: BlobUrl, type: str) -> None:
        content = await get_blob_content(blob["url"])

        langfuse_handler = CallbackHandler()
        chain = build_chain()
        summary_text = chain.invoke(
            {"content": content},
            config={"callbacks": [langfuse_handler]},
        ).content
        summary_json = json.dumps({"summary": summary_text}, ensure_ascii=False)
        self.store.context.create_context(
            thread_id=self.thread_id,
            opportunity_id=self.user_data.opportunity_id,
            user_id=self.user_data.user_id,
            channel=self.channel,
            type="summary",
            content=summary_json,
        )
