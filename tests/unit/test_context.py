import json
from datetime import timedelta
from typing import cast
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from echo.context.context import UserContext
from echo.context.types import Channel, Chat
from echo.store.store import PostgresStore

OPPORTUNITY_ID = "0063Y00001B8anuQAB"
INIT_CHANNEL: Channel = "voice"


@pytest_asyncio.fixture(scope="session")
async def seed_user(sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    async with sessionmaker() as session:
        store = PostgresStore(session)

        await store.users.upsert_user(
            user_id=uuid4(),
            opportunity_id=OPPORTUNITY_ID,
            contact_id="test_contact_id",
            name="Test",
            last_name="User",
        )

        await session.commit()


@pytest_asyncio.fixture
async def ctx(seed_user: None) -> UserContext:
    ctx = UserContext(
        opportunity_id=OPPORTUNITY_ID,
        channel=INIT_CHANNEL,
    )

    async with ctx:
        await populate_context(ctx)

    return ctx


@pytest.mark.asyncio
async def test_get_user_context(ctx: UserContext) -> None:
    async with ctx:
        res = await ctx.get_context(
            max_age=timedelta(days=3),
            channels=["voice", "whatsapp"],
            types=["chat", "summary"],
        )

    assert len(res) == 2


@pytest.mark.asyncio
async def test_get_user_context_by_type(ctx: UserContext) -> None:
    async with ctx:
        res = await ctx.get_context(types=["blob"])

    summary = json.loads(res[0].content)
    assert summary["url"] == "a blob url"


# Utils


async def populate_context(ctx: UserContext) -> None:
    await add_langchain_chat(ctx)
    await add_livekit_chat(ctx)
    await add_blob_url(ctx)


async def add_langchain_chat(ctx: UserContext) -> None:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_core.messages.utils import convert_to_openai_messages

    ctx.channel = "whatsapp"

    chat_langchain = [
        SystemMessage("a system prompt"),
        HumanMessage("a human msg"),
        AIMessage("an ai message"),
    ]
    chat = cast(Chat, convert_to_openai_messages(chat_langchain))
    await ctx.add_chat(chat)


async def add_livekit_chat(ctx: UserContext) -> None:
    from livekit.agents import ChatContext

    ctx.channel = "voice"

    livekit_ctx = ChatContext()
    livekit_ctx.add_message(role="developer", content="a dev msg")
    livekit_ctx.add_message(role="system", content="a sys prompt")
    livekit_ctx.add_message(role="user", content="an user msg")
    livekit_ctx.add_message(role="assistant", content="an ai msg")

    chat = cast(Chat, list(livekit_ctx.to_provider_format("openai")[0]))
    await ctx.add_chat(chat)


async def add_blob_url(ctx: UserContext) -> None:
    await ctx.add_blob({"url": "a blob url"})
