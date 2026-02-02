from uuid import uuid4

import pytest

import echo.events.v1 as events
from echo.utils.store import DuckDBStore, Store


@pytest.fixture
def db() -> Store:
    return DuckDBStore.in_memory()


ROOM_ID = str(uuid4())
OPPORTUNITY_ID = str(uuid4())


def test_end_room(db: Store) -> None:
    room_id = str(uuid4())
    opportunity_id = str(uuid4())

    start_event = events.SessionStarted(
        room_id=room_id,
        opportunity_id=opportunity_id,
    )

    db.set_room_start(
        room_id=start_event.room_id,
        opportunity_id=start_event.opportunity_id,
        start_time=start_event.timestamp,
    )

    end_event = events.SessionEnded(
        room_id=room_id,
        opportunity_id=opportunity_id,
        report_url="https://test.json",
    )

    db.set_room_end(
        room_id=start_event.room_id,
        end_time=start_event.timestamp,
    )

    db.set_room_report(room_id=room_id, report_url=end_event.report_url)
