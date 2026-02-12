from typing import Protocol, Self

import duckdb

from echo.store.analytics import AnalyticsTable
from echo.store.context import ContextTable
from echo.store.queries.postgres import ATTACH_POSTGRES_SQL, CREATE_POSTGRES_SECRET_SQL
from echo.store.rooms import RoomsTable
from echo.store.users import UsersTable


class Store(Protocol):
    rooms: RoomsTable
    users: UsersTable
    context: ContextTable
    analytics: AnalyticsTable


class DuckDBStore:
    def __init__(
        self,
        conn: duckdb.DuckDBPyConnection,
        is_postgres: bool = True,
        do_setup: bool = False,
    ) -> None:
        self.conn = conn
        self.rooms = RoomsTable(conn, is_postgres)
        self.users = UsersTable(conn, is_postgres)
        self.context = ContextTable(conn, is_postgres)
        self.analytics = AnalyticsTable(conn, is_postgres)

        if do_setup:
            self._setup_tables()

    @classmethod
    def with_postgres(cls, do_setup: bool = False) -> Self:
        conn = duckdb.connect(config={"threads": 1})
        conn.sql(CREATE_POSTGRES_SECRET_SQL)
        conn.sql(ATTACH_POSTGRES_SQL)
        return cls(
            conn=conn,
            is_postgres=True,
            do_setup=do_setup,
        )

    @classmethod
    def in_memory(cls, do_setup: bool = False) -> Self:
        conn = duckdb.connect(config={"threads": 1})
        return cls(
            conn=conn,
            is_postgres=False,
            do_setup=do_setup,
        )

    def _setup_tables(self) -> None:
        self.rooms.setup_table()
        self.users.setup_table()
        self.context.setup_table()
        self.analytics.setup_table()
