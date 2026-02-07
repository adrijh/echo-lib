from typing import Literal, TypedDict

type Channel = Literal["web", "whatsapp", "voice"]
type ContextType = Literal["chat", "blob", "summary"]


class ChatMessage(TypedDict):
    role: Literal["user", "system", "assistant"]
    content: str


type Chat = list[ChatMessage]


class BlobUrl(TypedDict):
    url: str
