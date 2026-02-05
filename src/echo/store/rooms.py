from datetime import datetime

import duckdb
from pydantic import BaseModel, field_serializer

from echo.store.queries import rooms as r


class RoomsRow(BaseModel):
    room_id: str
    opportunity_id: str
    start_time: datetime
    end_time: datetime | None
    report_url: str | None

    @field_serializer("start_time", "end_time")
    def serialize_unix_ts(self, v: datetime | None) -> float | None:
        if v is None:
            return None
        return v.timestamp()


class RoomsTable:
    def __init__(self, conn: duckdb.DuckDBPyConnection, is_postgres: bool) -> None:
        self.conn = conn
        self.table_name = "postgres.rooms" if is_postgres else "rooms"

    def setup_table(self) -> None:
        self.conn.sql(r.CREATE_ROOMS_TABLE_SQL.format(table_name=self.table_name))

    def set_room_start(
        self,
        room_id: str,
        opportunity_id: str,
        start_time: datetime,
    ) -> None:
        self.conn.execute(
            r.UPSERT_ROOM_SQL.format(table_name=self.table_name),
            (
                room_id,
                opportunity_id,
                start_time,
                None,
                None,
            ),
        )

    def set_room_end(
        self,
        room_id: str,
        end_time: datetime,
    ) -> None:
        self.conn.execute(
            r.UPSERT_ROOM_SQL.format(table_name=self.table_name),
            (
                room_id,
                None,
                None,
                end_time,
                None,
            ),
        )

    def set_room_report(self, room_id: str, report_url: str) -> None:
        self.conn.execute(
            r.UPSERT_ROOM_SQL.format(table_name=self.table_name),
            (
                room_id,
                None,
                None,
                None,
                report_url,
            ),
        )

    def get_rooms(self) -> list[RoomsRow]:
        data = self.conn.sql(r.LIST_ROOMS_SQL.format(table_name=self.table_name)).fetchall()
        return [
            RoomsRow(
                room_id=elem[0],
                opportunity_id=elem[1],
                start_time=elem[2],
                end_time=elem[3],
                report_url=elem[4],
            )
            for elem in data
        ]
