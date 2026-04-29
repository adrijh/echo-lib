import asyncio
import os
from typing import TYPE_CHECKING, Any

from echo.logger import get_logger
from echo.storage.base import Storage

if TYPE_CHECKING:
    from echo.storage.azure import AzureStorage
    from echo.storage.minio import MinioStorage

log = get_logger(__name__)

__all__ = ["AzureStorage", "MinioStorage", "Storage", "get_storage"]

_storage: Storage | None = None
_storage_lock = asyncio.Lock()


def __getattr__(name: str) -> Any:
    if name == "AzureStorage":
        from echo.storage.azure import AzureStorage

        return AzureStorage
    if name == "MinioStorage":
        from echo.storage.minio import MinioStorage

        return MinioStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


async def get_storage() -> Storage:
    global _storage

    if _storage is None:
        async with _storage_lock:
            if _storage is None:
                provider = os.getenv("STORAGE_BACKEND", "azure").lower()
                log.debug(f"loading storage for provider: {provider}...")

                if provider == "azure":
                    from echo.storage.azure import AzureStorage

                    _storage = AzureStorage()
                elif provider == "minio":
                    from echo.storage.minio import MinioStorage

                    _storage = MinioStorage()
                else:
                    raise ValueError(
                        f"Unknown STORAGE_PROVIDER: {provider!r} "
                        "(expected 'azure' or 'minio')"
                    )
    return _storage
