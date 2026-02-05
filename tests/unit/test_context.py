import json
from datetime import timedelta

import pytest

from echo.context.context import UserContext
from echo.store.store import DuckDBStore

OPPORTUNITY_ID = "0063Y00001B8anuQAB"
INIT_CHANNEL = "voice"


def populate_context(ctx: UserContext) -> None:
    add_langchain_chat(ctx)
    add_livekit_chat(ctx)
    add_blob_url(ctx)


def add_langchain_chat(ctx: UserContext) -> None:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_core.messages.utils import convert_to_openai_messages

    ctx.channel = "whatsapp"

    chat_langchain = [
        SystemMessage("a system prompt"),
        HumanMessage("a human msg"),
        AIMessage("an ai message"),
    ]
    chat = convert_to_openai_messages(chat_langchain)
    ctx.add_chat(chat)


def add_livekit_chat(ctx: UserContext) -> None:
    from livekit.agents import ChatContext

    ctx.channel = "voice"

    livekit_ctx = ChatContext()
    livekit_ctx.add_message(role="developer", content="a dev msg")
    livekit_ctx.add_message(role="system", content="a sys prompt")
    livekit_ctx.add_message(role="user", content="an user msg")
    livekit_ctx.add_message(role="assistant", content="an ai msg")

    chat = livekit_ctx.to_provider_format("openai")[0]
    ctx.add_chat(list(chat))


def add_blob_url(ctx: UserContext) -> None:
    ctx.add_summary({"url": "a blob url"})


@pytest.fixture
def ctx() -> UserContext:
    store = DuckDBStore.with_postgres(do_setup=True)
    ctx = UserContext.from_opportunity_id(
        store=store,
        opportunity_id=OPPORTUNITY_ID,
        channel=INIT_CHANNEL,
    )

    populate_context(ctx)
    return ctx


def test_get_user_context(ctx: UserContext) -> None:
    res = ctx.get_context(
        max_age=timedelta(days=3),
        channels=["voice", "whatsapp"],
        types=["chat", "summary"]

    )

    print(res)


def test_get_user_context_by_type(ctx: UserContext) -> None:
    res = ctx.get_context(types=["summary"])
    summary = json.loads(res[0].content)
    assert summary["url"] == "a blob url"
