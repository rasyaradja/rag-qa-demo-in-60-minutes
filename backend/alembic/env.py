"""
Alembic migration environment configuration for RAG Q&A Demo.

- Sets up Alembic context for running migrations with SQLAlchemy 2.0 async engine.
- Loads database URL from environment or backend/app/core/config.py.
- Imports all model metadata for autogenerate support.
- Supports both offline (SQL script) and online (DB) migration modes.
- Compatible with async SQLAlchemy models.

Usage:
    alembic upgrade head
    alembic revision --autogenerate -m "message"

"""

import asyncio
import logging
import sys
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# -- Ensure backend/app is importable for config and models --
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

# -- Import settings and models for metadata --
try:
    from core.config import settings
    from models.document import Base as DocumentBase
    from models.query import Base as QueryBase
    from models.eval import Base as EvalBase
except ImportError as e:
    raise ImportError(
        f"Could not import backend models or config: {e}. "
        "Ensure you run Alembic from the backend/ directory."
    )

# -- Alembic Config object, provides access to .ini values --
config = context.config

# -- Interpret the config file for Python logging --
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# -- Gather all model metadata for 'autogenerate' support --
target_metadata = [
    DocumentBase.metadata,
    QueryBase.metadata,
    EvalBase.metadata,
]

# -- Helper: Compose a single MetaData for Alembic autogenerate --
from sqlalchemy import MetaData

def merge_metadata(metadata_list):
    merged = MetaData()
    for meta in metadata_list:
        for table in meta.tables.values():
            table.tometadata(merged)
    return merged

merged_metadata = merge_metadata(target_metadata)

# -- Get DB URL from env or config --
def get_database_url():
    # Prefer env var, fallback to config
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    # settings.database_url may be a SecretStr
    db_url = getattr(settings, "database_url", None)
    if db_url is None:
        raise RuntimeError("DATABASE_URL not set in environment or config.")
    if hasattr(db_url, "get_secret_value"):
        return db_url.get_secret_value()
    return db_url

# -- Alembic offline mode (generates SQL scripts) --
def run_migrations_offline():
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=merged_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # For SQLite compatibility if needed
    )

    with context.begin_transaction():
        context.run_migrations()

# -- Alembic online mode (applies migrations to DB) --
def run_migrations_online():
    url = get_database_url()
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
        future=True,
    )

    async def do_run_migrations(connection: Connection):
        context.configure(
            connection=connection,
            target_metadata=merged_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    async def run():
        async with connectable.connect() as connection:
            await do_run_migrations(connection)
        await connectable.dispose()

    asyncio.run(run())

# -- Entrypoint: Choose offline/online mode --
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
