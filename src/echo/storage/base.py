from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from typing import Any, BinaryIO, Protocol


class Storage(Protocol):
    async def fetch_report(self, room_id: str) -> dict[str, Any]: ...

    async def fetch_recording(self, room_id: str) -> bytes | None: ...

    async def get_blob_content(self, blob_url: str, sas: bool = False) -> bytes | None: ...

    async def upload_report_with_retry(
        self,
        *,
        report: dict[str, Any],
        room_sid: str,
        max_attempts: int = 3,
        base_delay: float = 1.0,
    ) -> str | None: ...

    async def upload_report(
        self,
        report: dict[str, Any],
        room_sid: str,
    ) -> str | None: ...

    async def download_blobs_batch(
        self,
        blob_names: Sequence[str],
        dest_dir: Path,
        *,
        concurrency: int = 16,
    ) -> dict[str, Path]: ...

    async def upload_blob(
        self,
        blob_name: str,
        data: bytes | BinaryIO,
    ) -> str: ...

    async def stream_blob(self, url: str) -> AsyncIterator[bytes] | None: ...
