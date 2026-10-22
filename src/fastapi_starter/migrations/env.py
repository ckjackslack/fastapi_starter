"""Alembic environment (async). The database URL comes from the app settings."""

import asyncio

from alembic import context
from sqlalchemy.engine import Connection

from fastapi_starter import models  # noqa: F401  (registers tables on Base.metadata)
from fastapi_starter.config import get_settings
from fastapi_starter.db import Base, create_engine

config = context.config
target_metadata = Base.metadata


def database_url() -> str:
    return config.attributes.get("database_url") or get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # lets ALTER TABLE work on SQLite
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_engine(database_url())
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
