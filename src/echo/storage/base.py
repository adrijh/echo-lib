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


class TrackSource(TypedDict):
    blob_name: str
    started_at: int


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


def parse_track_filename(blob_name: str) -> dict[str, str]:
    base = blob_name.rsplit("/", 1)[-1]
    if base.endswith(".ogg"):
        base = base[:-4]
    parts = base.split("-")
    if len(parts) < 4:
        return {}
    return {
        "publisher_identity": "-".join(parts[:-3]),
        "track_source": parts[-3],
        "track_kind": parts[-2],
        "track_id": parts[-1],
    }


def extract_audio_paths(json_name: str, payload: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    files = payload.get("files")
    if isinstance(files, list):
        for entry in files:
            if isinstance(entry, dict):
                filename = entry.get("filename")
                if isinstance(filename, str):
                    paths.append(filename)
    if not paths and json_name.endswith(".ogg.json"):
        paths.append(json_name[:-5])
    return paths


def merge_track_metadata(
    blob_name: str,
    raw: dict[str, Any],
) -> dict[str, Any] | None:
    if "started_at" not in raw:
        return None
    parsed = parse_track_filename(blob_name)
    merged = {
        "started_at": int(raw["started_at"]),
        "track_id": raw.get("track_id") or parsed.get("track_id"),
        "publisher_identity": raw.get("publisher_identity") or parsed.get("publisher_identity"),
        "track_source": raw.get("track_source") or parsed.get("track_source"),
        "track_kind": raw.get("track_kind") or parsed.get("track_kind"),
    }
    if not all(merged.values()):
        return None
    return merged


class Storage(Protocol):
    async def fetch_report(self, room_id: str) -> dict[str, Any]: ...

    async def fetch_recording(self, room_id: str) -> bytes | None: ...

    async def fetch_recording_url(self, room_id: str) -> str | None: ...

    async def fetch_recording_tracks(self, room_id: str) -> list[TrackInfo]: ...

    async def list_recording_sources(self, room_id: str) -> list[TrackSource]: ...

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
