"""The database stack the whole project depends on. See ADR-002 and ADR-004.

These checks run against the real Postgres container - there is deliberately no
lighter engine to fall back on. They skip when DATABASE_URL is absent, so the
suite still runs in environments with no database.
"""

from collections.abc import Iterator
from urllib.parse import urlsplit, urlunsplit

import psycopg
import pytest

from app.config import settings_or_none

REQUIRED_EXTENSIONS = ("vector", "pg_trgm", "pgcrypto")

# Set by scripts/init_db.sql. Local development credentials only.
READ_ONLY_ROLE = "rl_readonly"
READ_ONLY_PASSWORD = "rl_readonly_pw"


def _dsn() -> str:
    """The app DSN, rewritten from SQLAlchemy form to something psycopg takes."""
    settings = settings_or_none()
    if settings is None:
        pytest.skip("no database is configured, so there is no database to check")
    return settings.database_url_psycopg


def _as_role(dsn: str, username: str, password: str) -> str:
    parts = urlsplit(dsn)
    host = parts.netloc.split("@")[-1]
    return urlunsplit((parts.scheme, f"{username}:{password}@{host}", parts.path, "", ""))


@pytest.fixture
def connection() -> Iterator[psycopg.Connection]:  # type: ignore[type-arg]
    with psycopg.connect(_dsn()) as conn:
        yield conn


def test_required_extensions_are_installed(connection: psycopg.Connection) -> None:  # type: ignore[type-arg]
    with connection.cursor() as cur:
        cur.execute("select extname from pg_extension")
        installed = {row[0] for row in cur.fetchall()}
    assert set(REQUIRED_EXTENSIONS) <= installed


def test_read_only_role_exists(connection: psycopg.Connection) -> None:  # type: ignore[type-arg]
    with connection.cursor() as cur:
        cur.execute("select 1 from pg_roles where rolname = %s", (READ_ONLY_ROLE,))
        assert cur.fetchone() is not None


def test_read_only_role_cannot_write() -> None:
    """ADR-004: the agent must be physically unable to change source data."""
    dsn = _as_role(_dsn(), READ_ONLY_ROLE, READ_ONLY_PASSWORD)
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        try:
            cur.execute("create table readonly_probe (id int)")
        except psycopg.errors.InsufficientPrivilege:
            return
        pytest.fail(f"{READ_ONLY_ROLE} was able to create a table")
