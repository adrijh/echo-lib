from typing import Any, Literal, TypedDict

type Channel = Literal["web", "whatsapp", "voice"]
type ContextType = Literal["chat", "blob"]
type Chat = list[dict[str, Any]]

class BlobUrl(TypedDict):
    url: str
