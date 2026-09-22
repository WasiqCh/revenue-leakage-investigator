"""The SQLAlchemy engine. See TICKET-004.

Plain-English: the one object that owns the connection pool to Postgres.

The driver is psycopg (v3). It speaks both sync and async, so the project needs
no second database driver -- AGENTS.md section 2 forbids adding a dependency
that is not already on the list, and psycopg is on it.

Both engines take the **same** DSN. What makes a connection asynchronous is the
factory used to create the engine (``create_async_engine``), not the URL. Alembic
and one-off scripts call ``create_engine`` on the same string.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import Settings, get_settings

# The one driver this project uses. Without the explicit prefix SQLAlchemy falls
# back to psycopg2, which is not installed.
PSYCOPG_PREFIX = "postgresql+psycopg://"
# Every other spelling of "Postgres" that a DSN may legitimately arrive in.
BARE_PREFIXES = ("postgresql://", "postgres://")
LEGACY_ASYNC_PREFIX = "postgresql+asyncpg://"


def to_psycopg_dsn(dsn: str) -> str:
    """Normalise any Postgres DSN into the psycopg form SQLAlchemy needs."""
    if dsn.startswith(PSYCOPG_PREFIX):
        return dsn
    for prefix in BARE_PREFIXES:
        if dsn.startswith(prefix):
            return PSYCOPG_PREFIX + dsn[len(prefix) :]
    if dsn.startswith(LEGACY_ASYNC_PREFIX):
        return PSYCOPG_PREFIX + dsn[len(LEGACY_ASYNC_PREFIX) :]
    raise ValueError(f"not a PostgreSQL DSN: {dsn!r}")


@lru_cache(maxsize=1)
def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return the process-wide async engine (created once)."""
    resolved = settings or get_settings()
    return create_async_engine(
        to_psycopg_dsn(resolved.database_url),
        pool_pre_ping=True,
        future=True,
    )


async def dispose_engine() -> None:
    """Close the pool. Called on shutdown and by tests."""
    engine = get_engine()
    await engine.dispose()
    get_engine.cache_clear()
