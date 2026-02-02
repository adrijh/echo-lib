from datetime import datetime
from typing import Any, Protocol, Self
from uuid import UUID

import duckdb

from echo.utils import queries as q

type StoreRow = tuple[UUID, UUID, datetime, datetime | None, str | None]

class Store(Protocol):
    def set_room_start(self, room_id: str, opportunity_id: str, start_time: datetime) -> None: ...
    def set_room_end(self, room_id: str, end_time: datetime) -> None: ...
    def set_room_report(self, room_id: str, report_url: str) -> None: ...
    def get_rooms(self) -> list[tuple[Any]]: ...


class DuckDBStore:
    def __init__(
        self,
        conn: duckdb.DuckDBPyConnection,
        table_name: str = "rooms"
    ) -> None:
        self.conn = conn
        self.table_name = table_name
        self._setup_tables()

    @classmethod
    def with_postgres(cls) -> Self:
        conn = duckdb.connect(config = {'threads': 1})
        conn.sql(q.CREATE_POSTGRES_SECRET_SQL)
        conn.sql(q.ATTACH_POSTGRES_SQL)
        return cls(
            conn=conn,
            table_name="postgres.rooms",
        )

    @classmethod
    def in_memory(cls) -> Self:
        conn = duckdb.connect(config = {'threads': 1})
        return cls(conn=conn, table_name="memory.rooms")

    def _setup_tables(self) -> None:
        self.conn.sql(q.CREATE_ROOMS_TABLE_SQL.format(table_name=self.table_name))

    def set_room_start(
        self,
        room_id: str,
        opportunity_id: str,
        start_time: datetime,
    ) -> None:
        self.conn.execute(
            q.UPSERT_ROOM_SQL.format(table_name=self.table_name),
            (
                room_id,
                opportunity_id,
                start_time,
                None,
                None,
            )
        )

    def set_room_end(
        self,
        room_id: str,
        end_time: datetime,
    ) -> None:
        self.conn.execute(
            q.UPSERT_ROOM_SQL.format(table_name=self.table_name),
            (
                room_id,
                None,
                None,
                end_time,
                None,
            )
        )

    def set_room_report(self, room_id: str, report_url: str) -> None:
        self.conn.execute(
            q.UPSERT_ROOM_SQL.format(table_name=self.table_name),
            (
                room_id,
                None,
                None,
                None,
                report_url,
            )
        )

    def get_rooms(self) -> list[tuple[Any]]:
        return self.conn.sql(q.LIST_ROOMS_SQL.format(table_name=self.table_name)).fetchall()
