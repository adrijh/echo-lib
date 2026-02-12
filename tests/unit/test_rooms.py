import json
from datetime import timedelta
from uuid import uuid4

import pytest

import echo.events.v1 as events
from echo.store.store import DuckDBStore, Store


@pytest.fixture
def db() -> Store:
    return DuckDBStore.with_postgres(do_setup=True)


def test_room_start(db: Store) -> None:
    room_id = str(uuid4())
    opportunity_id = str(uuid4())

    start_event = events.SessionStarted(
        room_id=room_id,
        opportunity_id=opportunity_id,
    )

    db.rooms.set_room_start(
        room_id=start_event.room_id,
        opportunity_id=start_event.opportunity_id,
        start_time=start_event.timestamp,
        thread_id=uuid4(),
    )

    rows = db.rooms.get_rooms()

    assert len(rows) == 1
    assert rows[0].room_id == start_event.room_id
    assert rows[0].opportunity_id == start_event.opportunity_id
    assert rows[0].start_time == start_event.timestamp


def test_room_start_end(db: Store) -> None:
    room_id = str(uuid4())
    opportunity_id = str(uuid4())

    start_event = events.SessionStarted(
        room_id=room_id,
        opportunity_id=opportunity_id,
    )
    end_time = start_event.timestamp + timedelta(minutes=5)
    report_url = "test"
    end_event = events.SessionEnded(
        room_id=room_id,
        opportunity_id=opportunity_id,
        timestamp=end_time,
        report_url=report_url,
    )

    db.rooms.set_room_start(
        room_id=start_event.room_id,
        opportunity_id=start_event.opportunity_id,
        start_time=start_event.timestamp,
        thread_id=uuid4(),
    )

    db.rooms.set_room_end(
        room_id=end_event.room_id,
        end_time=end_event.timestamp,
        thread_id=uuid4(),
        opportunity_id="000000",
    )

    db.rooms.set_room_report(
        room_id=end_event.room_id,
        report_url=end_event.report_url,
        opportunity_id="000000",
        thread_id=uuid4(),
    )

    rows = db.rooms.get_rooms()

    assert len(rows) == 2
    assert rows[0].room_id == end_event.room_id
    assert rows[0].opportunity_id == end_event.opportunity_id
    assert rows[0].start_time == start_event.timestamp
    assert rows[0].end_time == end_event.timestamp
    assert rows[0].report_url == end_event.report_url
