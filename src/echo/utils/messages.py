from typing import Any, cast

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    convert_to_openai_messages as langchain_messages_to_chat,
)

from echo.context.chain import build_chain
from echo.context.types import Chat


def livekit_report_to_chat(report: dict[str, Any]) -> Chat:
    events = report.get("events", [])

    messages: list[HumanMessage | AIMessage] = []

    for event in events:
        event_type = event.get("type")

        if event_type == "user_input_transcribed" and event.get("is_final"):
            text = event.get("transcript", "").strip()
            if text:
                messages.append(HumanMessage(text))

        if event_type == "conversation_item_added":
            item = event.get("item", {})
            if item.get("type") == "message" and item.get("role") == "assistant":
                parts = item.get("content", [])
                text = " ".join(parts).strip()
                if text:
                    messages.append(AIMessage(text))

    return cast(Chat, langchain_messages_to_chat(messages))


def build_summary(chat: Chat) -> str:
    chain = build_chain()
    summary = chain.invoke({"chat": chat})
    return cast(str, summary)
