from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, cast
from urllib.parse import quote

import aio_pika
import httpx
from aio_pika.abc import (
    AbstractChannel,
    AbstractQueue,
    AbstractRobustConnection,
)
from pamqp.commands import Queue as PamQueue

import echo.events.v1 as events
from echo.logger import get_logger

log = get_logger(__name__)


class Queue(Protocol):
    async def start(self, callback: Callable[[Any], Awaitable[Any]]) -> None: ...
    async def stop(self) -> None: ...

class RabbitManager:
    """Management-API client for RabbitMQ.

    Talks to the HTTP management plugin (default port 15672) rather than AMQP,
    since listing/inspecting queues server-side is only exposed there.
    """

    def __init__(
        self,
        host: str,
        management_port: int,
        username: str,
        password: str,
        vhost: str = "/",
        *,
        timeout: float = 10.0,
    ) -> None:
        self._vhost = vhost
        self._vhost_encoded = quote(vhost, safe="")
        self._client = httpx.AsyncClient(
            base_url=f"http://{host}:{management_port}",
            auth=(username, password),
            timeout=timeout,
        )

    @classmethod
    def from_env(cls) -> RabbitManager:
        return cls(
            host=os.environ["RABBITMQ_HOST"],
            management_port=int(os.environ.get("RABBITMQ_MANAGEMENT_PORT", "15672")),
            username=os.environ["RABBITMQ_USER"],
            password=os.environ["RABBITMQ_PASSWORD"],
            vhost=os.environ.get("RABBITMQ_VHOST", "/"),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> RabbitManager:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def list_queues(
        self,
        *,
        name_regex: str | None = None,
        columns: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List queues in the configured vhost, optionally filtered server-side."""
        params: dict[str, str] = {"pagination": "false"}
        if name_regex is not None:
            params["name"] = name_regex
            params["use_regex"] = "true"
        if columns:
            # The API supports trimming the payload — useful when you have thousands of queues.
            params["columns"] = ",".join(columns)

        resp = await self._client.get(
            f"/api/queues/{self._vhost_encoded}",
            params=params,
        )
        resp.raise_for_status()
        return cast(list[dict[str, Any]], resp.json())

    async def list_queues_with_prefix(
        self,
        prefix: str,
        *,
        columns: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List queues whose name starts with `prefix`."""
        # Escape regex metachars so '.' in 'echo.campaign.' isn't treated as a wildcard.
        import re
        escaped = re.escape(prefix)
        return await self.list_queues(name_regex=f"^{escaped}", columns=columns)

    async def queue_names_with_prefix(self, prefix: str) -> list[str]:
        """List queue names which start with `prefix`."""
        queues = await self.list_queues_with_prefix(prefix, columns=["name"])
        return [q["name"] for q in queues]

    async def get_queue(self, name: str) -> dict[str, Any]:
        resp = await self._client.get(
            f"/api/queues/{self._vhost_encoded}/{quote(name, safe='')}",
        )
        resp.raise_for_status()
        return cast(dict[str, Any], resp.json())

    async def purge_queue(self, name: str) -> None:
        resp = await self._client.delete(
            f"/api/queues/{self._vhost_encoded}/{quote(name, safe='')}/contents",
        )
        resp.raise_for_status()

    async def delete_queue(
        self,
        name: str,
        *,
        if_empty: bool = False,
        if_unused: bool = False,
    ) -> None:
        params: dict[str, str] = {}
        if if_empty:
            params["if-empty"] = "true"
        if if_unused:
            params["if-unused"] = "true"

        resp = await self._client.delete(
            f"/api/queues/{self._vhost_encoded}/{quote(name, safe='')}",
            params=params,
        )
        resp.raise_for_status()

    async def purge_queues_with_prefix(self, prefix: str) -> list[str]:
        """Purge every queue matching `prefix`. Returns the names that were purged."""
        names = await self.queue_names_with_prefix(prefix)
        for name in names:
            await self.purge_queue(name)
            log.info("purged queue", extra={"queue": name})
        return names


class RabbitConnection:
    def __init__(self, conn: AbstractRobustConnection) -> None:
        self._conn = conn
        self._channels: list[AbstractChannel] = []

    @classmethod
    async def connect(cls) -> RabbitConnection:
        conn = await aio_pika.connect_robust(
            host=os.environ["RABBITMQ_HOST"],
            port=int(os.environ["RABBITMQ_PORT"]),
            login=os.environ["RABBITMQ_USER"],
            password=os.environ["RABBITMQ_PASSWORD"],
        )
        return cls(conn)

    async def create_queue(
        self,
        name: str,
        *,
        prefetch: int = 1,
        durable: bool = False,
    ) -> RabbitQueue:
        channel = await self._conn.channel()
        await channel.set_qos(prefetch_count=prefetch)

        queue = await channel.declare_queue(name, durable=durable)

        self._channels.append(channel)

        return RabbitQueue(self, channel=channel, queue=queue)

    async def get_queue(
        self,
        name: str,
        *,
        prefetch: int = 1,
    ) -> RabbitQueue:
        channel = await self._conn.channel()
        await channel.set_qos(prefetch_count=prefetch)

        queue = await channel.get_queue(name)

        self._channels.append(channel)

        return RabbitQueue(self, channel=channel, queue=queue)

    async def close(self) -> None:
        for ch in self._channels:
            await ch.close()

        await self._conn.close()


class RabbitQueue:
    def __init__(
        self,
        conn: RabbitConnection,
        channel: AbstractChannel,
        queue: AbstractQueue,
    ) -> None:
        self.conn = conn
        self.channel = channel
        self.queue = queue

    async def stop(self) -> None:
        await self.channel.close()

    async def purge(self) -> PamQueue.PurgeOk:
        return await self.queue.purge()

    async def start(self, callback: Callable[[Any], Awaitable[Any]]) -> None:
        await self.queue.consume(callback)

    @staticmethod
    async def _get_queue_connection() -> AbstractRobustConnection:
        return await aio_pika.connect_robust(
            host=os.environ["RABBITMQ_HOST"],
            port=int(os.environ["RABBITMQ_PORT"]),
            login=os.environ["RABBITMQ_USER"],
            password=os.environ["RABBITMQ_PASSWORD"],
        )

    async def send_event(
        self,
        event: events.BaseEvent,
        delay_ms: int | None = None,
    ) -> None:
        body: bytes = event.model_dump_json().encode()

        message = aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
            expiration=delay_ms if delay_ms is not None else None,
        )

        await self.channel.default_exchange.publish(
            message,
            routing_key=self.queue.name,
        )

_manager: RabbitManager | None = None
_manager_lock = asyncio.Lock()

_connection: RabbitConnection | None = None
_queues: dict[str, RabbitQueue] = {}

_connection_lock = asyncio.Lock()
_queues_lock = asyncio.Lock()


async def get_queue_connection() -> RabbitConnection:
    global _connection

    if _connection is None:
        async with _connection_lock:
            if _connection is None:
                _connection = await RabbitConnection.connect()

    return _connection


async def get_queue(
    name: str,
    *,
    prefetch: int = 1,
    bootstrap: bool = False,
) -> RabbitQueue:
    if name not in _queues:
        async with _queues_lock:
            if name not in _queues:
                conn = await get_queue_connection()

                if bootstrap:
                    _queues[name] = await conn.create_queue(
                        name,
                        prefetch=prefetch,
                    )
                else:
                    _queues[name] = await conn.get_queue(
                        name,
                        prefetch=prefetch,
                    )

    return _queues[name]


async def get_rabbit_manager() -> RabbitManager:
    global _manager

    if _manager is None:
        async with _manager_lock:
            if _manager is None:
                _manager = RabbitManager.from_env()

    return _manager
