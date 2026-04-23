import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[Any] | None = None


def get_sessionmaker() -> async_sessionmaker[Any]:
    global _engine, _sessionmaker

    if _sessionmaker is None:
        _engine = create_engine()
        _sessionmaker = create_sessionmaker(_engine)

    return _sessionmaker


async def dispose_engine() -> None:
    global _engine, _sessionmaker

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None


def build_connection_string(
    *,
    user: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: str | None = None,
    database: str | None = None,
) -> str:
    user = user or os.environ["POSTGRES_USER"]
    password = password or os.environ["POSTGRES_PASSWORD"]
    host = host or os.environ["POSTGRES_HOST"]
    port = port or os.environ["POSTGRES_PORT"]
    database = database or os.environ["POSTGRES_DB"]

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


def build_dsn(
    *,
    user: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: str | None = None,
    database: str | None = None,
) -> str:
    user = user or os.environ["POSTGRES_USER"]
    password = password or os.environ["POSTGRES_PASSWORD"]
    host = host or os.environ["POSTGRES_HOST"]
    port = port or os.environ["POSTGRES_PORT"]
    database = database or os.environ["POSTGRES_DB"]

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def create_engine(connection_string: str | None = None) -> AsyncEngine:
    if not connection_string:
        connection_string = build_connection_string()

    return create_async_engine(
        connection_string,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )


def create_sessionmaker(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def session_scope(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
