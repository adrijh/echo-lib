import echo.events.v1 as events
from echo.worker.registry import register_handler


@register_handler(events.SessionStarted)
async def set_session_start(event: events.SessionStarted) -> None:
    pass


@register_handler(events.SessionEnded)
async def set_session_ended(event: events.SessionEnded) -> None:
    pass


@register_handler(events.SessionEnded)
async def create_session_summary(event: events.SessionEnded) -> None:
    # Parte de alfonso
    pass


@register_handler(events.StartSessionRequest)
async def start_call(event: events.StartSessionRequest) -> None:
    pass
