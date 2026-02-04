import asyncio

import echo.events.v1 as events
from echo.logger import configure_logger
from echo.services.sip import SipService
from echo.utils import db
from echo.worker.email_asesor.main import run_email_asesor_workflow
from echo.worker.registry import register_handler

log = configure_logger(__name__)
background_tasks: set[asyncio.Task[None]] = set()


@register_handler(events.SessionStarted)
async def set_session_start(event: events.SessionStarted) -> None:
    db.set_room_start(
        room_id=event.room_id,
        opportunity_id=event.opportunity_id,
        start_time=event.timestamp,
    )


@register_handler(events.SessionEnded)
async def set_session_ended(event: events.SessionEnded) -> None:
    db.set_room_end(
        room_id=event.room_id,
        end_time=event.timestamp,
    )

@register_handler(events.SessionEnded)
async def set_session_url(event: events.SessionEnded) -> None:
    db.set_room_report(
        room_id=event.room_id,
        report_url=event.report_url,
    )


@register_handler(events.SessionEnded)
async def create_session_summary(event: events.SessionEnded) -> None:
    event_payload = {
        "room_id": event.room_id,
        "session_blob": event.report_url,
    }

    await run_email_asesor_workflow(event_payload)


@register_handler(events.StartSessionRequest)
async def start_call(event: events.StartSessionRequest) -> None:
    log.info(f"[Handler] Received event for {event.phone_number}")

    service = SipService()
    room_name = f"room-{event.room_id}"

    try:
        can_proceed = await service.wait_until_line_free(event.phone_number)

        if not can_proceed:
            log.error("[Handler] Timeout waiting for free line. Discarding.")
            return

        room_name = await service.create_room_for_call(event)

        task = asyncio.create_task(SipService.run_background_call(room_name, event))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

        log.info("[Handler] Room reserved. Releasing RabbitMQ worker for next event.")

    except Exception as e:
        log.error(f"Error during reservation phase: {e}")
        await service.cleanup_room(room_name)
    finally:
        await service.close()
