import os
from typing import Self

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustConnection,
)

import echo.events.v1 as events
from echo.worker.registry import HANDLER_REGISTRY


class QueueWorker:
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
        conn = await QueueWorker.get_queue_connection()
        channel = await conn.channel()
        queue = await channel.declare_queue(os.environ["RABBITMQ_CHANNEL"])
        return cls(
            conn=conn,
            channel=channel,
            queue=queue,
        )

    async def stop(self) -> None:
        await self.channel.close()
        await self.conn.close()


    async def start(self) -> None:
        await self.queue.consume(self.handle_queue_message)

    @staticmethod
    async def get_queue_connection() -> AbstractRobustConnection:

        return await aio_pika.connect_robust(
            host=os.environ["RABBITMQ_HOST"],
            port=int(os.environ["RABBITMQ_PORT"]),
            login=os.environ["RABBITMQ_USER"],
            password=os.environ["RABBITMQ_PASSWORD"],
        )

    @staticmethod
    async def handle_queue_message(msg: AbstractIncomingMessage) -> None:
        async with msg.process():
            event = events.deserialize_event(msg.body)
            await QueueWorker.handle_event(event)

    @staticmethod
    async def handle_event(event: events.SessionEvent) -> None:
        for handler in HANDLER_REGISTRY.get(type(event), []):
            await handler(event)
