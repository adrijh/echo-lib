from datetime import datetime
import json
from typing import Any
import duckdb
from pydantic import BaseModel, field_serializer

from echo.store.queries import schedule_calls as sc


class ScheduleCallRow(BaseModel):
    opportunity_id: str
    scheduled_at: datetime
    metadata: dict[str, Any] | None
    status: str
    added_timestamp: datetime
    updated_timestamp: datetime

    @field_serializer(
        "scheduled_at",
        "added_timestamp",
        "updated_timestamp",
    )
    def serialize_ts(self, v: datetime | None) -> float | None:
        return None if v is None else v.timestamp()


class ScheduleCallsTable:
    def __init__(self, conn: duckdb.DuckDBPyConnection, is_postgres: bool) -> None:
        self.conn = conn
        self.table_name = (
            "postgres.schedule_calls" if is_postgres else "schedule_calls"
        )

    def setup_table(self) -> None:
        self.conn.sql(
            sc.CREATE_SCHEDULE_CALLS_TABLE_SQL.format(
                table_name=self.table_name
            )
        )
        self.conn.sql(
            sc.CREATE_SCHEDULE_CALLS_STATUS_INDEX_SQL.format(
                table_name=self.table_name
            )
        )
        self.conn.sql(
            sc.CREATE_SCHEDULE_CALLS_SCHEDULED_AT_INDEX_SQL.format(
                table_name=self.table_name
            )
        )

    def upsert_schedule_call(
        self,
        opportunity_id: str,
        scheduled_at: datetime,
        metadata: dict[str, Any] | None,
        status: str = "pending",
    ) -> None:
        self.conn.execute(
            sc.UPSERT_SCHEDULE_CALL_SQL.format(
                table_name=self.table_name
            ),
            (
                opportunity_id,
                scheduled_at,
                json.dumps(metadata) if metadata else None,
                status,
            ),
        )

    def get_ready_calls(self) -> list[ScheduleCallRow]:
        rows = self.conn.execute(
            sc.GET_READY_SCHEDULE_CALLS_SQL.format(
                table_name=self.table_name
            )
        ).fetchall()

        result = []
        for r in rows:
            result.append(
                ScheduleCallRow(
                    opportunity_id=r[0],
                    scheduled_at=r[1],
                    metadata=json.loads(r[2]) if r[2] else None,
                    status=r[3],
                    added_timestamp=r[4],
                    updated_timestamp=r[5],
                )
            )
        return result

    def mark_finished(self, opportunity_id: str) -> None:
        self.conn.execute(
            sc.UPDATE_SCHEDULE_CALL_STATUS_SQL.format(
                table_name=self.table_name
            ),
            ("finished", opportunity_id),
        )
