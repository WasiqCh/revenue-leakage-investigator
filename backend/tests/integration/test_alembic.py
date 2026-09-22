"""Alembic must be able to reach the database and agree with the models.

See TICKET-004. These are the two acceptance criteria that cannot be checked by
importing code: ``alembic upgrade head`` has to succeed, and ``alembic check``
has to find no difference between the migrations and the models. From TICKET-005
onwards there are real tables here, so this test is what stops a model being
added without a migration.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from app.config import settings_or_none

# backend/tests/integration/test_alembic.py -> backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="module", autouse=True)
def _require_database() -> None:
    if settings_or_none() is None:
        pytest.skip("no database is configured, so there is no database to migrate")


def test_alembic_upgrade_head_succeeds() -> None:
    result = _alembic("upgrade", "head")

    assert result.returncode == 0, f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}"


def test_alembic_check_finds_no_pending_model_changes() -> None:
    result = _alembic("check")

    assert result.returncode == 0, f"alembic check found pending changes:\n{result.stdout}"
    assert "No new upgrade operations detected" in result.stdout
