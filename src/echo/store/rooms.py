import json
from datetime import datetime
from typing import Any, cast
from uuid import UUID

import duckdb
from pydantic import BaseModel, field_serializer, field_validator

from echo.store.queries import rooms as r

type JsonType = dict[str, Any] | list[dict[str, Any]] | None

class RoomsRow(BaseModel):
    room_id: str
    opportunity_id: str
    thread_id: UUID
    start_time: datetime
    end_time: datetime | None
    report_url: str | None
    metadata: JsonType = None

    @field_serializer("start_time", "end_time")
    def serialize_unix_ts(self, v: datetime | None) -> float | None:
        if v is None:
            return None
        return v.timestamp()

    @field_validator("metadata", mode="before")
    @classmethod
    def deserialize_metadata(cls, v: str | None) -> dict[str, Any] | list[dict[str, Any]] | None:
        if v is None:
            return None

        if isinstance(v, str):
            return cast(JsonType, json.loads(v))


class RoomsTable:
    def __init__(self, conn: duckdb.DuckDBPyConnection, is_postgres: bool) -> None:
        self.conn = conn
        self.table_name = "postgres.rooms" if is_postgres else "rooms"

    def setup_table(self) -> None:
        self.conn.sql(r.CREATE_ROOMS_TABLE_SQL.format(table_name=self.table_name))

    def set_room_start(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        start_time: datetime,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.conn.execute(
            r.UPSERT_ROOM_SQL.format(table_name=self.table_name),
            (
                room_id,
                thread_id,
                opportunity_id,
                start_time,
                None,
                None,
                metadata,
            ),
        )

    def set_room_end(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        end_time: datetime,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.conn.execute(
            r.UPSERT_ROOM_SQL.format(table_name=self.table_name),
            (
                room_id,
                thread_id,
                opportunity_id,
                None,
                end_time,
                None,
                json.dumps(metadata) if metadata else None,
            ),
        )

    def set_room_report(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        report_url: str,
    ) -> None:
        self.conn.execute(
            r.UPSERT_ROOM_SQL.format(table_name=self.table_name),
            (
                room_id,
                thread_id,
                opportunity_id,
                None,
                None,
                report_url,
                None,
            ),
        )

    def get_rooms(self) -> list[RoomsRow]:
        data = self.conn.sql(r.LIST_ROOMS_SQL.format(table_name=self.table_name)).fetchall()
        return [
            RoomsRow(
                room_id=elem[0],
                thread_id=elem[1],
                opportunity_id=elem[2],
                start_time=elem[3],
                end_time=elem[4],
                report_url=elem[5],
                metadata=elem[6],
            )
            for elem in data
        ]
