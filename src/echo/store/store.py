from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Protocol, Self

from sqlalchemy.ext.asyncio import AsyncSession

from echo.db.base import get_sessionmaker
from echo.store.adversary import AdversaryTable
from echo.store.analytics import AnalyticsTable
from echo.store.context import ContextTable
from echo.store.rooms import RoomsTable
from echo.store.schedule_calls import ScheduleCallsTable
from echo.store.users import UsersTable


class Store(Protocol):
    rooms: RoomsTable
    users: UsersTable
    context: ContextTable
    analytics: AnalyticsTable
    schedule_calls: ScheduleCallsTable
    adversary: AdversaryTable


class PostgresStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.rooms = RoomsTable(session)
        self.users = UsersTable(session)
        self.context = ContextTable(session)
        self.analytics = AnalyticsTable(session)
        self.schedule_calls = ScheduleCallsTable(session)
        self.adversary = AdversaryTable(session)

    @classmethod
    @asynccontextmanager
    async def open(cls) -> AsyncGenerator[Self, None]:
        session = get_sessionmaker()()
        store = cls(session)
        try:
            yield store
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()
