"""The test suite must never touch the network. See AGENTS.md section 1.5.

These assertions are the guard rail for the ``env = [...]`` setting in
``backend/pyproject.toml``. That setting is inert unless ``pytest-env`` is
installed, and pytest only warns about the unknown key -- so without this test
the offline guarantee would silently disappear.
"""

import os


def test_llm_mock_is_set_for_the_whole_suite() -> None:
    assert os.environ.get("LLM_MOCK") == "1"


def test_cuad_offline_is_set_for_the_whole_suite() -> None:
    assert os.environ.get("CUAD_OFFLINE") == "1"
