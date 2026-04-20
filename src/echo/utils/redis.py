import os

from redis.asyncio import Redis


class RedisClient:
    _client: Redis | None = None

    @classmethod
    def get(cls) -> Redis:
        password = os.environ["REDIS_PASSWORD"]
        address = os.environ["REDIS_ADDRESS"]
        host = address.split(":")[0]
        port = address.split(":")[1]
        tls = os.getenv("REDIS_TLS", "true").lower() == "true"

        if cls._client is None:
            cls._client = Redis(
                host=host,
                port=int(port),
                password=password,
                ssl=tls,
            )

        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client:
            await cls._client.close()
            cls._client = None
