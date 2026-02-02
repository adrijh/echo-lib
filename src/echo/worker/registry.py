from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

import echo.events.v1 as events

type EventHandler[E] = Callable[[E], Coroutine[Any, Any, None]]

HANDLER_REGISTRY: dict[type[events.SessionEvent], list[EventHandler[Any]]] = defaultdict(list)

def register_handler[E: events.SessionEvent](event_type: type[E]) -> Callable[[EventHandler[E]], EventHandler[E]]:
    def decorator(func: EventHandler[E]) -> EventHandler[E]:
        HANDLER_REGISTRY[event_type].append(func)
        return func

    return decorator
