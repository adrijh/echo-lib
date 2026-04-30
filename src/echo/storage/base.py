from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from typing import Any, BinaryIO, Protocol, TypedDict


class TrackInfo(TypedDict):
    track_id: str
    publisher_identity: str
    track_source: str
    track_kind: str
    started_at: int
    role: str
    url: str


def derive_role(publisher_identity: str, track_source: str) -> str:
    if publisher_identity.startswith("sip"):
        return "user"
    if publisher_identity.startswith("agent"):
        if track_source == "microphone":
            return "agent"
        if track_source == "unknown":
            return "background"
    return "unknown"


def build_track_info(meta: dict[str, Any], url: str) -> TrackInfo:
    publisher_identity = meta["publisher_identity"]
    track_source = meta["track_source"]
    return TrackInfo(
        track_id=meta["track_id"],
        publisher_identity=publisher_identity,
        track_source=track_source,
        track_kind=meta["track_kind"],
        started_at=int(meta["started_at"]),
        role=derive_role(publisher_identity, track_source),
        url=url,
    )


class Storage(Protocol):
    async def fetch_report(self, room_id: str) -> dict[str, Any]: ...

    async def fetch_recording(self, room_id: str) -> bytes | None: ...

    async def fetch_recording_url(self, room_id: str) -> str | None: ...

    async def fetch_recording_tracks(self, room_id: str) -> list[TrackInfo]: ...

    async def get_blob_content(self, blob_url: str, sas: bool = False) -> bytes | None: ...

    async def get_blob_size(self, url: str) -> int | None: ...

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

    def stream_blob(self, url: str) -> AsyncIterator[bytes]: ...
