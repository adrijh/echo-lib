import os
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, Self

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustConnection,
)

import echo.events.v1 as events
from echo.logger import configure_logger
from echo.worker.registry import HANDLER_REGISTRY

log = configure_logger(__name__)


class Queue(Protocol):
    async def start(self, callback: Callable[[Any], Awaitable[Any]]) -> None: ...
    async def stop(self) -> None: ...


class RabbitQueue:
    def __init__(
        self,
        conn: AbstractRobustConnection,
        channel: AbstractChannel,
        queue: AbstractQueue,
    ) -> None:
        self.conn = conn
        self.channel = channel
        self.queue = queue

    @classmethod
    async def build(cls) -> Self:
        conn = await RabbitQueue._get_queue_connection()
        channel = await conn.channel()
        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue(os.environ["RABBITMQ_CHANNEL"], durable=False)
        return cls(
            conn=conn,
            channel=channel,
            queue=queue,
        )

    async def stop(self) -> None:
        await self.channel.close()
        await self.conn.close()

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

    async def send_event(self, event: events.SessionEvent) -> None:
        message = aio_pika.Message(
            body=event.model_dump_json().encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )

        await self.channel.default_exchange.publish(
            message,
            routing_key=self.queue.name,
        )


class QueueWorker:
    def __init__(self, queue: Queue) -> None:
        self.queue = queue

    async def start(self) -> None:
        await self.queue.start(self.handle_queue_message)

    async def stop(self) -> None:
        await self.queue.stop()

    @staticmethod
    async def handle_queue_message(msg: AbstractIncomingMessage) -> None:
        async with msg.process():
            event = events.deserialize_event(msg.body)
            await QueueWorker.handle_event(event)

    @staticmethod
    async def handle_event(event: events.SessionEvent) -> None:
        for handler in HANDLER_REGISTRY.get(type(event), []):
            log.info(f"handler: {handler.__name__}, event: {event}")
            await handler(event)
