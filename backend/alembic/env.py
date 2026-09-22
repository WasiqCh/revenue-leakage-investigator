"""Alembic environment. See TICKET-004.

Plain-English: this is the bridge between Alembic and our models. It tells
Alembic which database to use and which tables to compare against.

Migrations run **synchronously**, while the application uses the async engine.
Both read the same DSN from ``app.config`` and normalise it to psycopg.
"""

from __future__ import annotations

from importlib import import_module
from logging.config import fileConfig
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import engine_from_config, pool
from sqlalchemy.dialects.postgresql import TSVECTOR

from alembic import context
from app.config import get_settings
from app.db.base import Base
from app.db.engine import to_psycopg_dsn
from app.db.types import CurrencyCode, HalfOpenDateInterval, MoneyType

# Model packages are imported purely for their side effect of registering tables
# on Base.metadata. They only exist from TICKET-005 onwards, so missing ones are
# simply skipped.
MODEL_PACKAGES = (
    "app.models.source",
    "app.models.derived",
    "app.models.case",
    "app.models.ops",
)

for package in MODEL_PACKAGES:
    try:
        import_module(package)
    except ModuleNotFoundError:
        continue

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The URL comes from Settings, never from the ini file.
config.set_main_option("sqlalchemy.url", to_psycopg_dsn(get_settings().database_url))

target_metadata = Base.metadata


def render_item(type_: str, obj: object, autogen_context: Any) -> str | bool:
    """Render our custom column types as plain SQLAlchemy types.

    Plain-English: without this, autogenerate writes ``app.db.types.MoneyType``
    into the migration but forgets the import, and the migration crashes. It is
    also better practice for a migration to record the raw column type
    (``numeric(20, 4)``) than to import the application: a migration written
    today must keep producing the same DDL years from now, even if
    ``MoneyType`` has changed since.
    """
    if type_ != "type":
        return False
    if isinstance(obj, MoneyType):
        return f"sa.Numeric(precision={obj.precision}, scale={obj.scale})"
    if isinstance(obj, CurrencyCode):
        return f"sa.String(length={obj.length})"
    if isinstance(obj, HalfOpenDateInterval):
        autogen_context.imports.add("from sqlalchemy.dialects import postgresql")
        return "postgresql.DATERANGE()"
    # Same reason for pgvector: without this the migration says
    # `pgvector.sqlalchemy.vector.VECTOR(dim=1536)` with no import and dies.
    if isinstance(obj, Vector):
        autogen_context.imports.add("from pgvector.sqlalchemy import Vector")
        return f"Vector(dim={obj.dim})"
    if isinstance(obj, TSVECTOR):
        autogen_context.imports.add("from sqlalchemy.dialects import postgresql")
        return "postgresql.TSVECTOR()"
    return False


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of talking to the database."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_item=render_item,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
