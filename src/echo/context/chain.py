from typing import Any

from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSerializable

from echo.prompts import load_langfuse_prompt
from echo.utils.model import build_model


def build_chain() -> RunnableSerializable:
    sys_prompt_msg = load_langfuse_prompt("core/summarize")
    sys_prompt_tpl = SystemMessagePromptTemplate.from_template(sys_prompt_msg)
    human_prompt_tpl = HumanMessagePromptTemplate.from_template("{content}")
    model = build_model()

    prompt = ChatPromptTemplate(
        [sys_prompt_tpl, human_prompt_tpl],
        input_variables=["content"],
    )

    return format_input | prompt | model  # type: ignore


def format_input(input: dict[str, Any]) -> dict[str, Any]:
    events = input.get("content", [])

    messages: list[str] = []

    for event in events:
        event_type = event.get("type")

        if event_type == "user_input_transcribed" and event.get("is_final"):
            text = event.get("transcript", "").strip()
            if text:
                messages.append(f"Human: {text}")

        elif event_type == "conversation_item_added":
            item = event.get("item", {})
            if item.get("type") == "message" and item.get("role") == "assistant":
                parts = item.get("content", [])
                text = " ".join(parts).strip()
                if text:
                    messages.append(f"Assistant: {text}")

    return {
        "content": "\n\n".join(messages),
        **input,
    }
