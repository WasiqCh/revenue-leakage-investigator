"""DSN handling for the database engine. See TICKET-004.

Plain-English: one place decides which driver SQLAlchemy uses. If a DSN arrives
without a driver, SQL silently picks psycopg2 -- which is not installed -- and
the failure only shows up at connection time.
"""

from __future__ import annotations

import pytest

from app.db.engine import to_psycopg_dsn

CREDENTIALS = "rl_app:secret@localhost:5432/revenue_leakage"


def test_bare_postgres_dsn_gets_the_psycopg_driver() -> None:
    assert to_psycopg_dsn(f"postgresql://{CREDENTIALS}") == f"postgresql+psycopg://{CREDENTIALS}"


def test_legacy_postgres_scheme_is_normalised() -> None:
    assert to_psycopg_dsn(f"postgres://{CREDENTIALS}") == f"postgresql+psycopg://{CREDENTIALS}"


def test_a_dsn_that_already_names_psycopg_is_left_alone() -> None:
    dsn = f"postgresql+psycopg://{CREDENTIALS}"
    assert to_psycopg_dsn(dsn) == dsn


def test_an_asyncpg_dsn_falls_back_to_psycopg() -> None:
    """psycopg is the only driver we install, so anything else is rewritten."""
    assert (
        to_psycopg_dsn(f"postgresql+asyncpg://{CREDENTIALS}")
        == f"postgresql+psycopg://{CREDENTIALS}"
    )


def test_a_non_postgres_dsn_is_rejected_loudly() -> None:
    with pytest.raises(ValueError, match="not a PostgreSQL DSN"):
        to_psycopg_dsn("sqlite:///local.db")
