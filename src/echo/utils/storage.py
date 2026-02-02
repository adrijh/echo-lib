import os
from typing import cast

from azure.storage.blob.aio import BlobClient, ContainerClient

from echo.logger import configure_logger

logger = configure_logger(__name__)


async def get_blob_content(blob_url: str) -> str:
    account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

    conn_str = (
        "DefaultEndpointsProtocol=https;"
        f"AccountName={account_name};"
        f"AccountKey={account_key};"
        "EndpointSuffix=core.windows.net"
    )

    async with ContainerClient.from_connection_string(conn_str, container_name=container_name) as container_client:
        logger.info(f"Listing blobs in container '{container_name}':")
        async for blob in container_client.list_blobs():
            logger.info(f" -> Found Blob: '{blob.name}'")

    async with BlobClient.from_blob_url(blob_url, credential=account_key) as client:
        stream = await client.download_blob()
        content = await stream.readall()
        return cast(str, content.decode("utf-8"))
