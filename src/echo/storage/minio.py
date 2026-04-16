import asyncio
import json
import os
from typing import Any, cast
from urllib.parse import urlparse

from echo.logger import get_logger
from echo.storage.base import Storage

log = get_logger(__name__)

class MinioStorage(Storage):
    def __init__(self) -> None:
        import boto3

        self.client = boto3.client(
            "s3",
            endpoint_url=os.environ["MINIO_ENDPOINT"],
            aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
            aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
            region_name=os.environ["MINIO_REGION"],
        )

    async def fetch_report(self, room_id: str) -> dict[str, Any]:
        endpoint = os.environ["MINIO_ENDPOINT"].rstrip("/")
        bucket = os.environ["MINIO_BUCKET_SESSIONS"]
        blob_url = f"{endpoint}/{bucket}/recordings/{room_id}/session-report.json"

        log.info("Fetching report from URL: %s", blob_url)
        raw_bytes = await self.get_blob_content(blob_url)
        if raw_bytes is None:
            raise RuntimeError("Blob content could not be loaded")

        return cast(dict[str, Any], json.loads(raw_bytes.decode("utf-8")))

    async def fetch_recording(self, room_id: str) -> bytes | None:
        endpoint = os.environ["MINIO_ENDPOINT"].rstrip("/")
        bucket = os.environ["MINIO_BUCKET_SESSIONS"]
        blob_url = f"{endpoint}/{bucket}/recordings/{room_id}/recording.ogg"
        return await self.get_blob_content(blob_url)

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
                Bucket=os.environ["MINIO_BUCKET_SESSIONS"],
                Key=blob_name,
                Body=json_data,
                ContentType="application/json",
            )

            presigned_url = self.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": os.environ["MINIO_BUCKET_SESSIONS"],
                    "Key": blob_name,
                },
                ExpiresIn=86400,
            )

            log.debug(f"Session report uploaded to MinIO: {os.environ['MINIO_BUCKET_SESSIONS']}/{blob_name}")

            return cast(str | None, presigned_url)

        except Exception as e:
            log.error(f"Failed to upload session report to MinIO: {e}")
            return None
