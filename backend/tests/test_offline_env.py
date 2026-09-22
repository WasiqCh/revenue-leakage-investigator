"""The test suite must never touch the network. See AGENTS.md section 1.5.

These assertions are the guard rail for the ``env = [...]`` setting in
``backend/pyproject.toml``. That setting is inert unless ``pytest-env`` is
installed, and pytest only warns about the unknown key -- so without this test
the offline guarantee would silently disappear.

The values are read through ``app.config`` rather than from the process
environment directly, because config.py is the only module in the backend
allowed to look at environment variables.
"""

from __future__ import annotations

from app.config import get_settings


def test_llm_mock_is_set_for_the_whole_suite() -> None:
    assert get_settings().llm_mock is True


def test_cuad_offline_is_set_for_the_whole_suite() -> None:
    assert get_settings().cuad_offline is True
