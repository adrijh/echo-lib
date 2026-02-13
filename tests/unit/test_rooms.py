from datetime import timedelta
from dotenv import load_dotenv
from uuid import uuid4

import pytest

import echo.events.v1 as events
from echo.store.store import DuckDBStore, Store


load_dotenv()


@pytest.fixture
def db() -> Store:
    try:
        return DuckDBStore.with_postgres(do_setup=True)
    except Exception:
        print("Could not connect to Postgres, falling back to in-memory DuckDB")
        return DuckDBStore.in_memory(do_setup=True)


def test_room_start(db: Store) -> None:
    room_id = str(uuid4())
    opportunity_id = str(uuid4())
    thread_id = uuid4()

    start_event = events.SessionStarted(
        room_id=room_id,
        opportunity_id=opportunity_id,
    )
    metadata = {"key": "value"}

    db.rooms.set_room_start(
        room_id=start_event.room_id,
        thread_id=thread_id,
        opportunity_id=start_event.opportunity_id,
        start_time=start_event.timestamp,
        metadata=metadata,
    )

    rows = db.rooms.get_rooms()

    assert len(rows) == 1
    assert rows[0].room_id == start_event.room_id
    assert rows[0].opportunity_id == start_event.opportunity_id
    assert rows[0].thread_id == thread_id
    assert rows[0].start_time == start_event.timestamp
    assert rows[0].metadata == metadata


def test_room_start_end(db: Store) -> None:
    room_id = str(uuid4())
    opportunity_id = str(uuid4())
    thread_id = uuid4()

    start_event = events.SessionStarted(
        room_id=room_id,
        opportunity_id=opportunity_id,
    )
    metadata_start = {"key1": "value1"}
    end_time = start_event.timestamp + timedelta(minutes=5)
    report_url = "test"
    end_event = events.SessionEnded(
        room_id=room_id,
        opportunity_id=opportunity_id,
        timestamp=end_time,
        report_url=report_url,
    )
    metadata_end = {"key2": "value2"}

    db.rooms.set_room_start(
        room_id=start_event.room_id,
        thread_id=thread_id,
        opportunity_id=start_event.opportunity_id,
        start_time=start_event.timestamp,
        metadata=metadata_start,
    )

    db.rooms.set_room_end(
        room_id=end_event.room_id,
        thread_id=thread_id,
        opportunity_id=end_event.opportunity_id,
        end_time=end_event.timestamp,
        metadata=metadata_end,
    )

    db.rooms.set_room_report(
        room_id=end_event.room_id,
        thread_id=thread_id,
        opportunity_id=end_event.opportunity_id,
        report_url=end_event.report_url,
    )

    rows = db.rooms.get_rooms()

    assert len(rows) == 1
    assert rows[0].room_id == end_event.room_id
    assert rows[0].opportunity_id == end_event.opportunity_id
    assert rows[0].start_time == start_event.timestamp
    assert rows[0].end_time == end_event.timestamp
    assert rows[0].report_url == end_event.report_url
    assert rows[0].metadata == metadata_end
