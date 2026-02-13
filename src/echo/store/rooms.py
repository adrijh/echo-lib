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

    def _upsert(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        start_time: datetime | None,
        end_time: datetime | None,
        report_url: str | None,
        metadata: dict[str, str] | None,
    ) -> None:
        meta_json = json.dumps(metadata) if metadata else None

        # Log para depuración (opcional, pero ayuda)
        # print(f"UPSERT metadata (type {type(meta_json)}): {meta_json}")

        try:
            self.conn.execute(
                r.INSERT_ROOM_SQL.format(table_name=self.table_name),
                [ # Use list for parameters
                    room_id,
                    thread_id,
                    opportunity_id,
                    start_time,
                    end_time,
                    report_url,
                    meta_json,
                ],
            )
        except (duckdb.ConstraintException, duckdb.Error) as e:
             # Postgres scanner might raise generic Error for constraint violations
            if "duplicate key" in str(e) or "constraint" in str(e):
                # We skip updating metadata to avoid JSON type casting issues with DuckDB Postgres scanner.
                # Metadata is inserted correctly during creation and doesn't typically change.
                self.conn.execute(
                    r.UPDATE_ROOM_SQL.format(table_name=self.table_name),
                    [
                        start_time,
                        end_time,
                        report_url,
                        # meta_json, Removed from params
                        room_id,
                    ],
                )
            else:
                raise e

    def set_room_start(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        start_time: datetime,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self._upsert(
            room_id,
            thread_id,
            opportunity_id,
            start_time,
            None,
            None,
            metadata,
        )

    def set_room_end(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        end_time: datetime,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self._upsert(
            room_id,
            thread_id,
            opportunity_id,
            None,
            end_time,
            None,
            metadata,
        )

    def set_room_report(
        self,
        room_id: str,
        thread_id: UUID,
        opportunity_id: str,
        report_url: str,
    ) -> None:
        self._upsert(
            room_id,
            thread_id,
            opportunity_id,
            None,
            None,
            report_url,
            None,
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
