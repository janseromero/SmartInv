"""Alembic migration environment for SmartInv.

Resolves the database URL from application settings, registers the full model
metadata, and enables schema-aware autogenerate.
"""

from __future__ import annotations

import pathlib
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make the api package importable regardless of the invocation directory.
_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import api.db.models  # noqa: F401  (registers every model on the metadata)
from api.config import get_settings
from api.db.base import Base
from api.db.session import _to_psycopg_url

config = context.config
config.set_main_option("sqlalchemy.url", _to_psycopg_url(get_settings().database_url))

target_metadata = Base.metadata

# Schemas Alembic must manage. Its own version table lives in `public`.
MANAGED_SCHEMAS = (
    "core",
    "inventory",
    "sources",
    "ml",
    "agent",
    "workflow",
    "audit",
    "rag",
)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
