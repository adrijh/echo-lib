import asyncio
import os

from echo.logger import get_logger
from echo.storage.azure import AzureStorage
from echo.storage.base import Storage
from echo.storage.minio import MinioStorage

log = get_logger(__name__)

__all__ = ["AzureStorage", "MinioStorage"]

_storage: Storage| None = None
_storage_lock = asyncio.Lock()

async def get_storage() -> Storage:
    global _storage

    if _storage is None:
        async with _storage_lock:
            if _storage is None:
                provider = os.getenv("STORAGE_BACKEND", "azure").lower()
                log.debug(f"loading storage for provider: {provider}...")

                if provider == "azure":
                    _storage = AzureStorage()
                elif provider == "minio":
                    _storage = MinioStorage()
                else:
                    raise ValueError(
                        f"Unknown STORAGE_PROVIDER: {provider!r} "
                        "(expected 'azure' or 'minio')"
                    )
    return _storage
