from collections.abc import Sequence
from datetime import datetime
from textwrap import dedent
from typing import Any
from uuid import UUID

import duckdb
from pydantic import BaseModel, field_serializer

from echo.store.queries import users as u


class UserRow(BaseModel):
    user_id: UUID
    contact_id: str
    opportunity_id: str
    name: str | None
    last_name: str | None
    phone_number: str | None
    mail: str | None
    market: str | None
    faculty: str | None
    plancode: str | None
    track: str | None
    is_active: bool
    added_timestamp: datetime
    updated_timestamp: datetime

    @field_serializer("added_timestamp", "updated_timestamp")
    def serialize_unix_ts(self, v: datetime | None) -> float | None:
        return None if v is None else v.timestamp()


class UsersTable:
    def __init__(self, conn: duckdb.DuckDBPyConnection, is_postgres: bool) -> None:
        self.conn = conn
        self.table_name = "postgres.users" if is_postgres else "users"

    def setup_table(self) -> None:
        self.conn.sql(u.CREATE_USERS_TABLE_SQL.format(table_name=self.table_name))
        self.conn.sql(u.CREATE_USER_ID_INDEX_SQL.format(table_name=self.table_name))
        self.conn.sql(u.CREATE_OPPORTUNITY_ID_INDEX_SQL.format(table_name=self.table_name))

    def upsert_user(
        self,
        user_id: str,
        contact_id: str | None = None,
        opportunity_id: str | None = None,
        name: str | None = None,
        last_name: str | None = None,
        phone_number: str | None = None,
        mail: str | None = None,
        market: str | None = None,
        faculty: str | None = None,
        plancode: str | None = None,
        track: str | None = None,
    ) -> None:
        self.conn.execute(
            u.UPSERT_USER_SQL.format(table_name=self.table_name),
            (
                user_id,
                contact_id,
                opportunity_id,
                name,
                last_name,
                phone_number,
                mail,
                market,
                faculty,
                plancode,
                track,
            ),
        )

    def soft_delete_user(self, user_id: str) -> None:
        self.conn.execute(
            u.SOFT_DELETE_USER_SQL.format(table_name=self.table_name),
            (user_id,),
        )

    def get_users(self) -> list[UserRow]:
        rows = self.conn.sql(u.LIST_USERS_SQL.format(table_name=self.table_name)).fetchall()

        return [
            UserRow(
                user_id=r[0],
                contact_id=r[1],
                opportunity_id=r[2],
                name=r[3],
                last_name=r[4],
                phone_number=r[5],
                mail=r[6],
                market=r[7],
                faculty=r[8],
                plancode=r[9],
                track=r[10],
                is_active=r[11],
                added_timestamp=r[12],
                updated_timestamp=r[13],
            )
            for r in rows
        ]

    def get_user(
        self,
        *,
        user_id: str | None = None,
        contact_id: str | None = None,
        opportunity_id: str | None = None,
    ) -> UserRow | None:
        if user_id is None and contact_id is None and opportunity_id is None:
            raise ValueError("get_user requires user_id, contact_id, or opportunity_id")

        row = self.conn.execute(
            u.GET_USER_BY_IDENTIFIER_SQL.format(table_name=self.table_name),
            (
                user_id,
                contact_id,
                opportunity_id,
            ),
        ).fetchone()

        if row is None:
            return None

        return UserRow(
            user_id=row[0],
            contact_id=row[1],
            opportunity_id=row[2],
            name=row[3],
            last_name=row[4],
            phone_number=row[5],
            mail=row[6],
            market=row[7],
            faculty=row[8],
            plancode=row[9],
            track=row[10],
            is_active=row[11],
            added_timestamp=row[12],
            updated_timestamp=row[13],
        )

    def query_users(
        self,
        where_clause: str = "",
        params: Sequence[Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[UserRow]:
        sql = dedent(f"""
        SELECT
            user_id,
            contact_id,
            opportunity_id,
            name,
            last_name,
            phone_number,
            mail,
            market,
            faculty,
            plancode,
            track,
            is_active,
            added_timestamp,
            updated_timestamp
        FROM {self.table_name}
        """)

        if where_clause:
            sql += f" WHERE {where_clause}"

        if limit is not None:
            sql += " LIMIT ?"
            params = (*params, limit) if params else (limit,)

        if offset is not None:
            sql += " OFFSET ?"
            params = (*params, offset) if params else (offset,)

        rows = self.conn.execute(sql, params or ()).fetchall()

        return [UserRow(**self._row_to_dict(r)) for r in rows]

    def _row_to_dict(self, r: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "user_id": r[0],
            "contact_id": r[1],
            "opportunity_id": r[2],
            "name": r[3],
            "last_name": r[4],
            "phone_number": r[5],
            "mail": r[6],
            "market": r[7],
            "faculty": r[8],
            "plancode": r[9],
            "track": r[10],
            "is_active": r[11],
            "added_timestamp": r[12],
            "updated_timestamp": r[13],
        }
