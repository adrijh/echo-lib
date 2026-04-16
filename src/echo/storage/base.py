from typing import Any, Protocol


class Storage(Protocol):
    async def fetch_report(self, room_id: str) -> dict[str, Any]: ...
    async def fetch_recording(self, room_id: str) -> bytes | None: ...
    async def get_blob_content(self, blob_url: str, sas: bool = False) -> bytes | None: ...
    async def upload_report_with_retry(
        self,
        *,
        report: dict[str, Any],
        room_sid: str,
        max_attempts: int,
        base_delay: float,
    ) -> str | None: ...
    async def upload_report(
        self,
        report: dict[str, Any],
        room_sid: str,
    ) -> str | None: ...
