from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import duckdb
from pydantic import BaseModel, field_serializer

from echo.context.types import Channel, ContextType
from echo.store.queries import context as c


class ContextRow(BaseModel):
    context_id: str
    thread_id: UUID
    opportunity_id: str
    user_id: UUID
    channel: Channel
    content: str
    type: ContextType
    added_timestamp: datetime
    updated_timestamp: datetime

    @field_serializer("added_timestamp", "updated_timestamp")
    def serialize_unix_ts(self, v: datetime | None) -> float | None:
        if v is None:
            return None
        return v.timestamp()


class ContextTable:
    def __init__(self, conn: duckdb.DuckDBPyConnection, is_postgres: bool) -> None:
        self.conn = conn
        self.table_name = "postgres.context" if is_postgres else "context"
        self.is_postgres = is_postgres

    def setup_table(self) -> None:

        # self.conn.sql(c.CREATE_CONTEXT_TYPE_ENUM_SQL)
        # self.conn.sql(c.CREATE_CHANNEL_TYPE_ENUM_SQL)
        self.conn.sql(c.CREATE_CONTEXT_TABLE_SQL.format(table_name=self.table_name))

        # if self.is_postgres:
        #     self.conn.sql(c.CREATE_CONTEXT_INDEXES_SQL.format(table_name=self.table_name))
        #
    def create_context(
        self,
        thread_id: UUID,
        opportunity_id: str,
        user_id: UUID,
        channel: Channel,
        content: str,
        type: ContextType,
    ) -> None:
        context_id = uuid4()
        self.conn.execute(
            c.INSERT_CONTEXT_SQL.format(table_name=self.table_name),
            (
                context_id,
                thread_id,
                opportunity_id,
                user_id,
                channel,
                content,
                type,
            ),
        )

    def update_content(
        self,
        context_id: UUID,
        content: list[dict[str, Any]],
    ) -> None:
        self.conn.execute(
            c.UPDATE_CONTEXT_CONTENT_SQL.format(table_name=self.table_name),
            (
                content,
                context_id,
            ),
        )

    def get_context_by_id(self, context_id: UUID) -> ContextRow | None:
        row = self.conn.execute(
            c.GET_CONTEXT_BY_ID_SQL.format(table_name=self.table_name),
            (context_id,),
        ).fetchone()

        if row is None:
            return None

        return ContextRow(
            context_id=row[0],
            thread_id=row[1],
            opportunity_id=row[2],
            user_id=row[3],
            channel=row[4],
            content=row[5],
            type=row[6],
            added_timestamp=row[7],
            updated_timestamp=row[8],
        )

    def get_contexts(self) -> list[ContextRow]:
        rows = self.conn.sql(
            c.LIST_CONTEXTS_SQL.format(table_name=self.table_name)
        ).fetchall()

        return [
            ContextRow(
                context_id=r[0],
                thread_id=r[1],
                opportunity_id=r[2],
                user_id=r[3],
                channel=r[4],
                content=r[5],
                type=r[6],
                added_timestamp=r[7],
                updated_timestamp=r[8],
            )
            for r in rows
        ]

    def get_context_history(
        self,
        *,
        user_id: UUID | None = None,
        opportunity_id: str | None = None,
        max_age: timedelta = timedelta(days=30),
        types: list[ContextType] | None = None,
        channels: list[Channel] | None = None,
    ) -> list[ContextRow]:

        if user_id is None and opportunity_id is None:
            raise ValueError(
                "get_context_history requires either user_id or opportunity_id"
            )

        if max_age <= timedelta(0):
            raise ValueError("max_age must be a positive timedelta")

        conditions: list[str] = []
        params: list[Any] = []

        min_ts = datetime.now(UTC) - max_age
        conditions.append("added_timestamp >= ?")
        params.append(min_ts)

        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)

        if opportunity_id is not None:
            conditions.append("opportunity_id = ?")
            params.append(opportunity_id)

        if types:
            placeholders = ", ".join("?" for _ in types)
            conditions.append(f"type IN ({placeholders})")
            params.extend(types)

        if channels:
            placeholders = ", ".join("?" for _ in channels)
            conditions.append(f"channel IN ({placeholders})")
            params.extend(channels)

        where_clause = " AND ".join(conditions)

        sql = c.FETCH_CONTEXT_HISTORY_BASE_SQL.format(
            table_name=self.table_name,
            where_clause=where_clause,
        )

        rows = self.conn.execute(sql, params).fetchall()

        return [
            ContextRow(
                context_id=r[0],
                thread_id=r[1],
                opportunity_id=r[2],
                user_id=r[3],
                channel=r[4],
                content=r[5],
                type=r[6],
                added_timestamp=r[7],
                updated_timestamp=r[8],
            )
            for r in rows
        ]
