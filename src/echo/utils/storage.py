import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import urlparse

from azure.storage.blob.aio import BlobClient, BlobServiceClient
from typing_extensions import deprecated

from echo.logger import get_logger

log = get_logger(__name__)


@deprecated("Use storage class")
async def fetch_report(url: str) -> dict[str, Any]:
    log.info("Fetching report from URL: %s", url)
    raw_bytes = await get_blob_content(url, True)
    if raw_bytes is None:
        raise RuntimeError("Blob content could not be loaded")

    return cast(dict[str, Any], json.loads(raw_bytes.decode("utf-8")))


@deprecated("Use storage class")
async def get_blob_content(blob_url: str, sas: bool = False) -> bytes | None:
    storage_backend = os.getenv("STORAGE_BACKEND", "azure")

    if storage_backend == "azure":
        return await get_azure_blob_content(blob_url, sas)

    if storage_backend == "minio":
        return await get_minio_blob_content(blob_url)

    return None


@deprecated("Use storage class")
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


@deprecated("Use storage class")
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


@deprecated("Use storage class")
async def upload_report_with_retry(
    *,
    report: dict[str, Any],
    room_sid: str,
    max_attempts: int = 3,
    base_delay: float = 1.0,
) -> str | None:
    for attempt in range(1, max_attempts + 1):
        try:
            file_url = await upload_report_to_blob_storage(
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


@deprecated("Use storage class")
async def upload_report_to_blob_storage(
    report: dict[str, Any],
    room_sid: str,
) -> str | None:

    storage_backend = os.getenv("STORAGE_BACKEND", "azure")
    current_date = datetime.now().strftime("%Y-%m-%dT%H%M%S")

    if storage_backend == "local":
        filename = f"{room_sid}-{current_date}-session-report.json"
        output_dir = "data/output"
        os.makedirs(output_dir, exist_ok=True)
        local_path = f"{output_dir}/{filename}"

        with open(local_path, "w") as f:
            json.dump(report, f, indent=2)

        log.debug(f"Session report saved locally to {local_path}")
        return f"file://{os.path.abspath(local_path)}"

    if storage_backend == "azure":
        return await upload_report_to_azure_blob_storage(report, room_sid)

    if storage_backend == "minio":
        return upload_report_to_minio_blob_storage(report, room_sid)

    return None


@deprecated("Use storage class")
async def upload_report_to_azure_blob_storage(
    report: dict[str, Any],
    room_sid: str,
) -> str | None:
    from azure.storage.blob import BlobSasPermissions, generate_blob_sas

    json_data = json.dumps(report, indent=2)
    container = os.environ["AZURE_STORAGE_CONTAINER_SESSIONS_NAME"]
    blob_name = f"recordings/{room_sid}/session-report.json"

    try:
        blob_service_client = BlobServiceClient.from_connection_string(os.environ["AZURE_STORAGE_CONNECTION_STRING"])

        container_client = blob_service_client.get_container_client(os.environ["AZURE_STORAGE_CONTAINER_SESSIONS_NAME"])

        await container_client.upload_blob(blob_name, json_data, overwrite=True)

        account_name = blob_service_client.account_name
        sas_token = generate_blob_sas(
            account_name=account_name,  # type: ignore[arg-type]
            container_name=container,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(UTC) + timedelta(hours=24),
        )

        log.debug(f"Session report uploaded to Azure Storage: {container}/{blob_name}")

        return f"https://{account_name}.blob.core.windows.net/{container}/{blob_name}?{sas_token}"

    except Exception as e:
        log.error(f"Failed to upload session report to Azure: {e}")
        return None


@deprecated("Use storage class")
def upload_report_to_minio_blob_storage(
    report: dict[str, Any],
    room_sid: str,
) -> str | None:
    json_data = json.dumps(report, indent=2)
    blob_name = f"recordings/{room_sid}/session-report.json"

    try:
        import boto3

        s3 = boto3.client(
            "s3",
            endpoint_url=os.environ["MINIO_ENDPOINT"],
            aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
            aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
            region_name=os.environ["MINIO_REGION"],
        )

        s3.put_object(
            Bucket=os.environ["MINIO_BUCKET_SESSIONS"],
            Key=blob_name,
            Body=json_data,
            ContentType="application/json",
        )

        presigned_url = s3.generate_presigned_url(
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
