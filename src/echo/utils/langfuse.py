import asyncio

from langfuse import get_client
from langfuse._client.client import Langfuse

_langfuse: Langfuse | None = None
_langfuse_lock = asyncio.Lock()


async def get_langfuse_client() -> Langfuse:
    global _langfuse

    if _langfuse is None:
        async with _langfuse_lock:
            if _langfuse is None:
                _langfuse = get_client()

    return _langfuse
