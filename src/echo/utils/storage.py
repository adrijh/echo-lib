import os

from azure.storage.blob.aio import BlobClient

from echo.logger import configure_logger

log = configure_logger(__name__)


async def get_blob_content(blob_url: str, sas: bool = False) -> bytes | None:
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
            return await stream.readall()

    except Exception:
        log.exception(f"Could not download blob with url '{blob_url}'")
        return None
