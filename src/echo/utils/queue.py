from __future__ import annotations

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
from echo.logger import configure_logger

log = configure_logger(__name__)


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

    async def send_event(self, event: events.BaseEvent) -> None:
        message = aio_pika.Message(
            body=event.model_dump_json().encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await self.channel.default_exchange.publish(
            message,
            routing_key=self.queue.name,
        )
