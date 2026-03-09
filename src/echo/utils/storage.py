import asyncio
import json
import os
from typing import Any, cast
from urllib.parse import urlparse

from azure.storage.blob.aio import BlobClient

from echo.logger import get_logger

log = get_logger(__name__)


async def fetch_report(url: str) -> dict[str, Any]:
    log.info("Fetching report from URL: %s", url)
    raw_bytes = await get_blob_content(url, True)
    if raw_bytes is None:
        raise RuntimeError("Blob content could not be loaded")

    return cast(dict[str, Any], json.loads(raw_bytes.decode("utf-8")))


async def get_blob_content(blob_url: str, sas: bool = False) -> bytes | None:
    storage_backend = os.getenv("STORAGE_BACKEND", "azure")

    if storage_backend == "azure":
        return await get_azure_blob_content(blob_url, sas)

    if storage_backend == "minio":
        return await get_minio_blob_content(blob_url)

    return None


async def get_azure_blob_content(blob_url: str, sas: bool = False) -> bytes | None:
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
        log.error(f"Could not download blob with url '{blob_url}'")
        return None


async def get_minio_blob_content(blob_url: str) -> bytes | None:
    import boto3

    try:
        parsed = urlparse(blob_url)
        bucket = parsed.path.split("/")[1]
        key = "/".join(parsed.path.split("/")[2:])

        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["MINIO_ENDPOINT"],
            aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
            aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
            region_name=os.environ["MINIO_REGION"],
        )

        def _download() -> Any:
            response = s3.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()

        return await asyncio.to_thread(_download)

    except Exception:
        log.error(f"Could not download object with url '{blob_url}'")
        return None
