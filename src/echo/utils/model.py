import os

from langchain_openai import (
    AzureChatOpenAI,
    ChatOpenAI,
)
from pydantic import SecretStr

from echo import config as cfg
from echo.logger import configure_logger

logger = configure_logger(__name__)

type ChatModel = ChatOpenAI | AzureChatOpenAI


OPENAI = "openai"
AZURE = "azure"


def _build_openai_chat(model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
    )


def _build_azure_chat(deployment: str) -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_deployment=deployment,
        api_key=SecretStr(os.environ["AZURE_OPENAI_KEY"]),
        api_version=os.getenv("OPENAI_API_VERSION", "2024-12-01-preview"),
        reasoning_effort="none",
    )


def build_model() -> ChatModel:
    if cfg.LLM_PROVIDER == OPENAI:
        return _build_openai_chat(os.environ["OPENAI_MODEL"])

    if cfg.LLM_PROVIDER == AZURE:
        return _build_azure_chat(os.environ["AZURE_OPENAI_DEPLOYMENT"])

    raise ValueError


def build_mini_model() -> ChatModel:
    if cfg.LLM_PROVIDER == OPENAI:
        return _build_openai_chat(os.environ["OPENAI_MODEL_MINI"])

    if cfg.LLM_PROVIDER == AZURE:
        return _build_azure_chat(os.environ["AZURE_OPENAI_DEPLOYMENT_MINI"])

    raise ValueError
