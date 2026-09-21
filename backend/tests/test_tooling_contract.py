"""The tooling contract declared in ``backend/pyproject.toml``.

AGENTS.md section 2 pins Python 3.13, ruff and strict mypy. These tests fail
loudly if one of those settings is relaxed by accident.
"""

import sys
import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _config() -> dict:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)


def _dev_dependency_names() -> set[str]:
    """Dependency names without version specifiers: "ruff>=0.6" -> "ruff"."""
    names: set[str] = set()
    for raw in _config()["project"]["optional-dependencies"]["dev"]:
        name = raw.split("[")[0]
        for splitter in ("=", ">", "<", "!", ";", "~"):
            name = name.split(splitter)[0]
        names.add(name.strip().lower())
    return names


def test_python_version_matches_the_pinned_runtime() -> None:
    assert sys.version_info >= (3, 13)
    assert "3.13" in _config()["project"]["requires-python"]


def test_offline_guard_plugin_is_declared() -> None:
    assert "pytest-env" in _dev_dependency_names()


def test_required_tooling_is_declared() -> None:
    assert {"pytest", "pytest-asyncio", "hypothesis", "ruff", "mypy"} <= _dev_dependency_names()


def test_ruff_line_length_is_the_agreed_width() -> None:
    assert _config()["tool"]["ruff"]["line-length"] == 100


def test_mypy_runs_strict() -> None:
    assert _config()["tool"]["mypy"]["strict"] is True


def test_pytest_declares_the_offline_environment() -> None:
    declared = _config()["tool"]["pytest"]["ini_options"]["env"]
    assert "LLM_MOCK=1" in declared
    assert "CUAD_OFFLINE=1" in declared


def test_pytest_collects_from_the_tests_directory() -> None:
    assert _config()["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]
