from datetime import timedelta
from uuid import uuid4

import pytest
from dotenv import load_dotenv

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
    pass
