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
    service = SipService()
    room_name = f"room-{event.room_id}"

    try:
        ai_number = await service.allocate_resources(event.phone_number)

        if not ai_number:
            log.error("Timeout waiting for resources. Discarding.")
            return

        room_name = await service.create_room_for_call(event, ai_number)

        task = asyncio.create_task(SipService.run_background_call(room_name, event, ai_number))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    except Exception as e:
        log.error(f"Error during reservation phase: {e}")
        await service.cleanup_room(room_name)
    finally:
        await service.close()
