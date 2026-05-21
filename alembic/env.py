import asyncio
from logging.config import fileConfig
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import MetaData, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from echo.db.base import build_connection_string

ENV_FILE = Path(__file__).parent / ".." / ".env"
load_dotenv(ENV_FILE)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Which schema this run targets, chosen by the active config section
# (`alembic --name <section>`). Empty/absent means the core schema, which
# keeps the historical behaviour: default search_path and the alembic_version
# table in the connection's default schema.
TARGET_SCHEMA = config.get_main_option("target_schema") or None


def get_target_metadata() -> MetaData:
    if TARGET_SCHEMA == "agents":
        from echo.db.agents import models  # noqa: F401  (registers tables)
        from echo.db.agents.base import Base

        return Base.metadata

    import echo.db  # noqa: F401  (registers core models)
    from echo.db.base import Base
    from echo.db.models import adversary  # noqa: F401

    return Base.metadata


target_metadata = get_target_metadata()


def include_object(
    obj: Any,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: Any,
) -> bool:
    # Don't let autogenerate drop reflected tables that aren't part of our
    # metadata (e.g. langgraph checkpoint/store tables sharing the schema).
    if type_ == "table" and reflected and name not in target_metadata.tables:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=build_connection_string(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        version_table_schema=TARGET_SCHEMA,
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        version_table_schema=TARGET_SCHEMA,
        include_schemas=False,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations against a connection."""
    connect_args: dict[str, Any] = {}
    if TARGET_SCHEMA:
        # Pin the migration connection to the target schema only. Without this
        # reflection sees every search-path-visible table (all of `public`),
        # producing spurious drops against unrelated tables. asyncpg applies
        # this as a connection parameter rather than libpq `options`.
        connect_args["server_settings"] = {"search_path": TARGET_SCHEMA}

    connectable = create_async_engine(
        build_connection_string(),
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
