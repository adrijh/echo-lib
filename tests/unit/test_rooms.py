from collections.abc import AsyncIterator
from datetime import timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import echo.events.v1 as events
from echo.store.store import PostgresStore, Store

load_dotenv()


@pytest_asyncio.fixture
async def store(sessionmaker: async_sessionmaker[AsyncSession]) -> AsyncIterator[Store]:
    async with sessionmaker() as session:
        yield PostgresStore(session)


@pytest.mark.asyncio
async def test_room_start(store: PostgresStore) -> None:
    room_id = str(uuid4())
    opportunity_id = str(uuid4())
    thread_id = uuid4()

    start_event = events.SessionStarted(
        room_id=room_id,
        opportunity_id=opportunity_id,
    )
    metadata = {"key": "value"}

    await store.rooms.set_room_start(
        room_id=start_event.room_id,
        thread_id=thread_id,
        opportunity_id=start_event.opportunity_id,
        start_timestamp=start_event.timestamp,
        metadata=metadata,
    )

    await store.session.commit()

    rows = await store.rooms.get_rooms()

    assert len(rows) == 1
    assert rows[0].room_id == start_event.room_id
    assert rows[0].opportunity_id == start_event.opportunity_id
    assert rows[0].thread_id == thread_id
    assert rows[0].start_timestamp == start_event.timestamp
    assert rows[0].metadata_ == metadata


@pytest.mark.asyncio
async def test_room_start_end(store: PostgresStore) -> None:
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

    await store.rooms.set_room_start(
        room_id=start_event.room_id,
        thread_id=thread_id,
        opportunity_id=start_event.opportunity_id,
        start_timestamp=start_event.timestamp,
        metadata=metadata_start,
    )
    await store.session.commit()

    await store.rooms.set_room_end(
        room_id=end_event.room_id,
        thread_id=thread_id,
        opportunity_id=end_event.opportunity_id,
        end_timestamp=end_event.timestamp,
        metadata=metadata_end,
    )
    await store.session.commit()

    await store.rooms.set_room_report(
        room_id=end_event.room_id,
        thread_id=thread_id,
        opportunity_id=end_event.opportunity_id,
        report_url=end_event.report_url,
    )

    await store.session.commit()

    rows = await store.rooms.get_rooms()

    assert len(rows) == 2
    assert rows[-1].room_id == end_event.room_id
    assert rows[-1].opportunity_id == end_event.opportunity_id
    assert rows[-1].start_timestamp == start_event.timestamp
    assert rows[-1].end_timestamp == end_event.timestamp
    assert rows[-1].report_url == end_event.report_url
    assert rows[-1].metadata_ == metadata_end
