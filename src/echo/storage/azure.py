import asyncio
import json
import os
from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO, cast

from azure.storage.blob.aio import BlobClient, BlobServiceClient

from echo.logger import get_logger
from echo.storage.base import Storage

log = get_logger(__name__)

class AzureStorage(Storage):
    def __init__(self) -> None:
        self.account_name = os.environ["AZURE_ACCOUNT_NAME"]
        self.sessions_container_name = os.environ["AZURE_STORAGE_CONTAINER_SESSIONS_NAME"]
        self.service_client = BlobServiceClient.from_connection_string(
            os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        )
        self.sessions_client = self.service_client.get_container_client(
            self.sessions_container_name
        )

    async def fetch_report(self, room_id: str, sas: bool = False) -> dict[str, Any]:
        blob_url = f"https://{self.account_name}.blob.core.windows.net/{self.sessions_container_name}/recordings/{room_id}/session-report.json"

        log.info("Fetching report from URL: %s", blob_url)
        raw_bytes = await self.get_blob_content(blob_url, sas)
        if raw_bytes is None:
            raise RuntimeError("Blob content could not be loaded")

        return cast(dict[str, Any], json.loads(raw_bytes.decode("utf-8")))


    async def fetch_recording(self, room_id: str) -> bytes | None:
        blob_url = f"https://{self.account_name}.blob.core.windows.net/{self.sessions_container_name}/recordings/{room_id}/recording.ogg"
        content = await self.get_blob_content(blob_url)
        return content


    async def get_blob_content(self, blob_url: str, sas: bool = False) -> bytes | None:
        try:
            if sas:
                client = BlobClient.from_blob_url(blob_url)
            else:
                client = BlobClient.from_blob_url(
                    blob_url,
                    credential=os.environ["AZURE_ACCOUNT_KEY"],
                )

            async with client:
                stream = await client.download_blob()
                return cast(bytes | None, await stream.readall())

        except Exception:
            log.warning(f"Could not download blob with url '{blob_url}'")
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
        from azure.storage.blob import BlobSasPermissions, generate_blob_sas

        json_data = json.dumps(report, indent=2)
        container = os.environ["AZURE_STORAGE_CONTAINER_SESSIONS_NAME"]
        blob_name = f"recordings/{room_sid}/session-report.json"

        try:
            await self.sessions_client.upload_blob(blob_name, json_data, overwrite=True)

            account_name = self.service_client.account_name
            sas_token = generate_blob_sas(
                account_name=account_name,  # type: ignore[arg-type]
                container_name=container,
                blob_name=blob_name,
                account_key=self.service_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(UTC) + timedelta(hours=24),
            )

            log.debug(f"Session report uploaded to Azure Storage: {container}/{blob_name}")

            return f"https://{account_name}.blob.core.windows.net/{container}/{blob_name}?{sas_token}"

        except Exception as e:
            log.error(f"Failed to upload session report to Azure: {e}")
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

        async def _download_one(blob_name: str) -> None:
            async with sem:
                try:
                    local_path = dest_dir / blob_name.replace("/", "_")
                    blob_client = self.sessions_client.get_blob_client(blob_name)
                    async with blob_client:
                        stream = await blob_client.download_blob()
                        data = await stream.readall()
                    local_path.write_bytes(data)
                    results[blob_name] = local_path
                except Exception:
                    log.warning(f"Failed to download blob: {blob_name}", exc_info=True)

        await asyncio.gather(*(_download_one(name) for name in blob_names))
        log.info(f"Downloaded {len(results)}/{len(blob_names)} blobs to {dest_dir}")
        return results

    async def upload_blob(
        self,
        blob_name: str,
        data: bytes | BinaryIO,
    ) -> str:
        try:
            await self.sessions_client.upload_blob(blob_name, data, overwrite=True)
            log.debug(f"Uploaded blob: {self.sessions_container_name}/{blob_name}")
            return (
                f"https://{self.account_name}.blob.core.windows.net"
                f"/{self.sessions_container_name}/{blob_name}"
            )
        except Exception:
            log.exception(f"Failed to upload blob: {blob_name}")
            raise

    async def stream_blob(self, url: str) -> AsyncIterator[bytes]:
        blob_client = BlobClient.from_blob_url(
            url,
            credential=os.environ["AZURE_ACCOUNT_KEY"],
        )
        async with blob_client:
            stream = await blob_client.download_blob()
            async for chunk in stream.chunks():
                yield chunk

    async def get_blob_size(self, url: str) -> int | None:
        try:
            blob_client = BlobClient.from_blob_url(
                url, credential=os.environ["AZURE_ACCOUNT_KEY"],
            )
            async with blob_client:
                props = await blob_client.get_blob_properties()
                return props.size
        except Exception:
            return None
