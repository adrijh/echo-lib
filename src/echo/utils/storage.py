import os

from azure.storage.blob.aio import BlobClient

from echo.logger import configure_logger

log = configure_logger(__name__)


async def get_blob_content(blob_url: str) -> bytes | None:
    async with BlobClient.from_blob_url(blob_url, credential=os.environ["AZURE_ACCOUNT_KEY"]) as client:

        try:
            stream = await client.download_blob()
            content = await stream.readall()
            return content
        except Exception as e:
            log.error(f"Could not download blob with url '{blob_url}': {e}")
            return None
