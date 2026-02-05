from typing import Any, TypedDict

type Chat = list[dict[str, Any]]

class BlobUrl(TypedDict):
    url: str
