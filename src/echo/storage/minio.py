import asyncio
import json
import os
from collections.abc import AsyncIterator, Sequence
from pathlib import Path
from typing import Any, BinaryIO, cast
from urllib.parse import urlparse

from echo.logger import get_logger
from echo.storage.base import (
    Storage,
    TrackInfo,
    TrackSource,
    build_track_info,
    extract_audio_paths,
    merge_track_metadata,
)

log = get_logger(__name__)


class MinioStorage(Storage):
    def __init__(self) -> None:
        import boto3

        self.endpoint = os.environ["MINIO_ENDPOINT"].rstrip("/")
        public_endpoint = os.environ.get("MINIO_PUBLIC_ENDPOINT", self.endpoint).rstrip("/")
        self.sessions_bucket = os.environ["MINIO_BUCKET_SESSIONS"]

        creds = {
            "aws_access_key_id": os.environ["MINIO_ACCESS_KEY"],
            "aws_secret_access_key": os.environ["MINIO_SECRET_KEY"],
            "region_name": os.environ["MINIO_REGION"],
        }
        self.client = boto3.client("s3", endpoint_url=self.endpoint, **creds)
        self.presign_client = (
            self.client
            if public_endpoint == self.endpoint
            else boto3.client("s3", endpoint_url=public_endpoint, **creds)
        )

    async def fetch_report(self, room_id: str) -> dict[str, Any]:
        blob_url = f"{self.endpoint}/{self.sessions_bucket}/recordings/{room_id}/session-report.json"

        log.info("Fetching report from URL: %s", blob_url)
        raw_bytes = await self.get_blob_content(blob_url)
        if raw_bytes is None:
            raise RuntimeError("Blob content could not be loaded")

        return cast(dict[str, Any], json.loads(raw_bytes.decode("utf-8")))

    async def fetch_recording(self, room_id: str) -> bytes | None:
        blob_url = f"{self.endpoint}/{self.sessions_bucket}/recordings/{room_id}/recording.ogg"
        return await self.get_blob_content(blob_url)

    async def fetch_recording_url(self, room_id: str) -> str | None:
        key = f"recordings/{room_id}/recording.ogg"

        def _head_and_sign() -> str | None:
            try:
                self.client.head_object(Bucket=self.sessions_bucket, Key=key)
            except Exception:
                return None
            return cast(
                str,
                self.presign_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.sessions_bucket, "Key": key},
                    ExpiresIn=86400,
                ),
            )

        return await asyncio.to_thread(_head_and_sign)

    async def fetch_recording_tracks(self, room_id: str) -> list[TrackInfo]:
        entries = await self._list_track_metadata(room_id)

        tracks: list[TrackInfo] = []
        for ogg_key, meta in entries:
            try:
                url = self.presign_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.sessions_bucket, "Key": ogg_key},
                    ExpiresIn=86400,
                )
                tracks.append(build_track_info(meta, url))
            except (KeyError, TypeError) as exc:
                log.warning(f"Skipping track {ogg_key}: {exc}")

        return tracks

    async def list_recording_sources(self, room_id: str) -> list[TrackSource]:
        entries = await self._list_track_metadata(room_id)
        return [TrackSource(blob_name=blob_name, started_at=int(meta["started_at"])) for blob_name, meta in entries]

    async def _list_track_metadata(self, room_id: str) -> list[tuple[str, dict[str, Any]]]:
        prefix = f"recordings/{room_id}/tracks/"

        def _list_keys() -> tuple[list[str], list[str]]:
            ogg_keys: list[str] = []
            json_keys: list[str] = []
            paginator = self.client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.sessions_bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith(".json"):
                        json_keys.append(key)
                    elif key.endswith(".ogg"):
                        ogg_keys.append(key)
            return ogg_keys, json_keys

        ogg_keys, json_keys = await asyncio.to_thread(_list_keys)

        payloads = await asyncio.gather(*(self._download_sidecar(name) for name in json_keys))

        meta_by_audio: dict[str, dict[str, Any]] = {}
        for json_key, payload in zip(json_keys, payloads, strict=True):
            if payload is None:
                continue
            for audio_path in extract_audio_paths(json_key, payload):
                meta_by_audio[audio_path] = payload

        entries: list[tuple[str, dict[str, Any]]] = []
        for ogg_key in ogg_keys:
            raw = meta_by_audio.get(ogg_key)
            if raw is None:
                log.warning(f"No sidecar metadata for track {ogg_key}, skipping")
                continue
            merged = merge_track_metadata(ogg_key, raw)
            if merged is None:
                log.warning(f"Incomplete sidecar metadata for {ogg_key}, skipping")
                continue
            entries.append((ogg_key, merged))

        entries.sort(key=lambda e: int(e[1]["started_at"]))
        return entries

    async def _download_sidecar(self, key: str) -> dict[str, Any] | None:
        try:

            def _get() -> bytes:
                response = self.client.get_object(Bucket=self.sessions_bucket, Key=key)
                return cast(bytes, response["Body"].read())

            data = await asyncio.to_thread(_get)
            return cast(dict[str, Any], json.loads(data.decode("utf-8")))
        except Exception:
            log.warning(f"Failed to load sidecar: {key}", exc_info=True)
            return None

    async def get_blob_content(self, blob_url: str, sas: bool = False) -> bytes | None:
        try:
            parsed = urlparse(blob_url)
            bucket = parsed.path.split("/")[1]
            key = "/".join(parsed.path.split("/")[2:])

            def _download() -> Any:
                response = self.client.get_object(Bucket=bucket, Key=key)
                return response["Body"].read()

            return await asyncio.to_thread(_download)

        except Exception:
            log.error(f"Could not download object with url '{blob_url}'")
            return None

    async def upload_report_with_retry(
        self,
        *,
        report: dict[str, Any],
        room_sid: str,
        max_attempts: int = 3,
        base_delay: float = 1.0,
    ) -> str | None:
        for attempt in range(1, max_attempts + 1):
            try:
                file_url = await self.upload_report(
                    report=report,
                    room_sid=room_sid,
                )
                if file_url:
                    return file_url

                log.warning(
                    "Upload attempt %s/%s returned no file_url (room_sid=%s)",
                    attempt,
                    max_attempts,
                    room_sid,
                )

            except Exception as exc:
                log.exception(
                    "Upload attempt %s/%s failed (room_sid=%s): %s",
                    attempt,
                    max_attempts,
                    room_sid,
                    exc,
                )

            if attempt < max_attempts:
                await asyncio.sleep(base_delay * (2 ** (attempt - 1)))

        return None

    async def upload_report(
        self,
        report: dict[str, Any],
        room_sid: str,
    ) -> str | None:
        json_data = json.dumps(report, indent=2)
        blob_name = f"recordings/{room_sid}/session-report.json"

        try:
            self.client.put_object(
                Bucket=self.sessions_bucket,
                Key=blob_name,
                Body=json_data,
                ContentType="application/json",
            )

            presigned_url = self.presign_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.sessions_bucket,
                    "Key": blob_name,
                },
                ExpiresIn=86400,
            )

            log.debug(f"Session report uploaded to MinIO: {self.sessions_bucket}/{blob_name}")

            return cast(str | None, presigned_url)

        except Exception as e:
            log.error(f"Failed to upload session report to MinIO: {e}")
            return None

    async def download_blobs_batch(
        self,
        blob_names: Sequence[str],
        dest_dir: Path,
        *,
        concurrency: int = 16,
    ) -> dict[str, Path]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        sem = asyncio.Semaphore(concurrency)
        results: dict[str, Path] = {}
        results_lock = asyncio.Lock()

        async def _download_one(key: str) -> None:
            async with sem:
                try:
                    local_path = dest_dir / key.replace("/", "_")

                    def _fetch() -> bytes:
                        response = self.client.get_object(Bucket=self.sessions_bucket, Key=key)
                        return cast(bytes, response["Body"].read())

                    data = await asyncio.to_thread(_fetch)
                    local_path.write_bytes(data)
                    async with results_lock:
                        results[key] = local_path
                except Exception:
                    log.warning(f"Failed to download object: {key}", exc_info=True)

        await asyncio.gather(*(_download_one(name) for name in blob_names))
        log.info(f"Downloaded {len(results)}/{len(blob_names)} objects to {dest_dir}")
        return results

    async def upload_blob(
        self,
        blob_name: str,
        data: bytes | BinaryIO,
    ) -> str:
        try:

            def _upload() -> None:
                self.client.put_object(
                    Bucket=self.sessions_bucket,
                    Key=blob_name,
                    Body=data,
                )

            await asyncio.to_thread(_upload)
            log.debug(f"Uploaded object: {self.sessions_bucket}/{blob_name}")
            return f"{self.endpoint}/{self.sessions_bucket}/{blob_name}"
        except Exception:
            log.exception(f"Failed to upload object: {blob_name}")
            raise

    async def stream_blob(self, url: str) -> AsyncIterator[bytes]:
        parsed = urlparse(url)
        bucket = parsed.path.split("/")[1]
        key = "/".join(parsed.path.split("/")[2:])

        response = await asyncio.to_thread(self.client.get_object, Bucket=bucket, Key=key)
        body = response["Body"]

        try:
            while True:
                chunk = await asyncio.to_thread(body.read, 8192)
                if not chunk:
                    break
                yield chunk
        finally:
            body.close()

    async def get_blob_size(self, url: str) -> int | None:
        try:
            parsed = urlparse(url)
            bucket = parsed.path.split("/")[1]
            key = "/".join(parsed.path.split("/")[2:])

            def _head() -> int:
                response = self.client.head_object(Bucket=bucket, Key=key)
                return cast(int, response["ContentLength"])

            return await asyncio.to_thread(_head)
        except Exception:
            log.error(f"Could not get size for object with url '{url}'")
            return None
