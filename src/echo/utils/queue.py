from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import aio_pika
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
