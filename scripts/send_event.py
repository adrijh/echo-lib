import asyncio
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

ENV_FILE = Path(__file__).parent / ".." / ".env"
load_dotenv(ENV_FILE)

from echo.events import v1 as events
from echo.worker.queue import RabbitQueue


async def send_event(event: events.SessionEvent) -> None:
    queue = await RabbitQueue.build()
    await queue.send_event(event)
    await queue.stop()


if __name__ == "__main__":
    event = events.StartSessionRequest(
        room_id=str(uuid4()),
        opportunity_id=str(uuid4()),
        phone_number="+34665886861",
        participant_name="Lukitas",
    )
    asyncio.run(send_event(event))
