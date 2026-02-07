from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.runnables import RunnableSerializable

from echo.context.types import Chat
from echo.prompts import load_prompt_by_name
from echo.utils.model import build_model


def build_chain() -> RunnableSerializable[dict[str, Chat], str]:
    sys_prompt_msg = load_prompt_by_name("summarize")
    sys_prompt_tpl = SystemMessagePromptTemplate.from_template(sys_prompt_msg)
    human_prompt_tpl = HumanMessagePromptTemplate.from_template("{content}")
    model = build_model()

    prompt = ChatPromptTemplate(
        [sys_prompt_tpl, human_prompt_tpl],
        input_variables=["content"],
    )

    return format_input | prompt | model | StrOutputParser()


def format_input(input: dict[str, Chat]) -> dict[str, Any]:
    chat = input["chat"]
    text = ""
    for message in chat:
        if not message["content"]:
            continue

        text += f"{message["role"]}: {message["content"]}\n"

    return {
        "content": text,
        **input,
    }
