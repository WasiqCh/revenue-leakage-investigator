"""Settings contract. See TICKET-003.

These tests prove four things:

1. A missing ``DATABASE_URL`` is a loud validation error that names the field.
2. The defaults for tolerances and confidence weights still match the numbers
   published in the docs.
3. Boolean flags and DSNs are parsed the way the rest of the stack expects.
4. Nothing outside ``app/config.py`` reads ``os.environ``.

The suite stays offline: ``LLM_MOCK=1`` comes from pytest-env.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import (
    DOCUMENTED_CONFIDENCE_WEIGHTS,
    DOCUMENTED_MONEY_TOLERANCE_ABS,
    DOCUMENTED_MONEY_TOLERANCE_PCT,
    Settings,
)

TEST_DATABASE_URL = "postgresql+psycopg://rl_app:secret@localhost:5432/revenue_leakage"


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Give the settings object the one field that is always required."""
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    yield


def _weights_from_settings(settings: Settings) -> dict[str, Decimal]:
    return {
        "evidence_completeness": settings.confidence_weight_evidence_completeness,
        "source_agreement": settings.confidence_weight_source_agreement,
        "deterministic_certainty": settings.confidence_weight_deterministic_certainty,
        "contract_clarity": settings.confidence_weight_contract_clarity,
        "exception_absence": settings.confidence_weight_exception_absence,
        "data_freshness": settings.confidence_weight_data_freshness,
        "historical_precedent": settings.confidence_weight_historical_precedent,
        "amount_materiality": settings.confidence_weight_amount_materiality,
    }


def _find_docs_confidence() -> Path | None:
    """Locate docs/confidence.md, walking up from this test file.

    Inside the container only ``backend/`` is mounted, so the docs are not
    always reachable. Callers skip when this returns None.
    """
    here = Path(__file__).resolve()
    for parent in here.parents[:4]:
        candidate = parent / "docs" / "confidence.md"
        if candidate.is_file():
            return candidate
    return None


def _parse_documented_weights(path: Path) -> dict[str, Decimal]:
    """Read the published factor table, e.g. ``| `source_agreement` | 0.20 |``."""
    pattern = re.compile(r"\|\s*`([a-z_]+)`\s*\|\s*(0\.\d+)\s*\|")
    found: dict[str, Decimal] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.search(line)
        if match and match.group(1) not in found:
            found[match.group(1)] = Decimal(match.group(2))
    return found


def test_missing_database_url_raises_naming_the_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError) as excinfo:
        Settings()  # type: ignore[call-arg]

    assert "database_url" in str(excinfo.value)


def test_money_tolerance_defaults_match_the_docs(env: None) -> None:
    settings = Settings()  # type: ignore[call-arg]

    assert settings.money_tolerance_abs == DOCUMENTED_MONEY_TOLERANCE_ABS == Decimal("1.00")
    assert settings.money_tolerance_pct == DOCUMENTED_MONEY_TOLERANCE_PCT == Decimal("0.005")


def test_confidence_weight_defaults_match_the_constants(env: None) -> None:
    settings = Settings()  # type: ignore[call-arg]

    assert _weights_from_settings(settings) == DOCUMENTED_CONFIDENCE_WEIGHTS
    assert sum(DOCUMENTED_CONFIDENCE_WEIGHTS.values(), Decimal(0)) == Decimal("1.00")


def test_confidence_weight_defaults_match_the_docs_file(env: None) -> None:
    path = _find_docs_confidence()
    if path is None:
        pytest.skip("docs/ is not mounted in this container")

    documented = _parse_documented_weights(path)
    assert len(documented) == len(DOCUMENTED_CONFIDENCE_WEIGHTS), (
        f"expected {len(DOCUMENTED_CONFIDENCE_WEIGHTS)} factors in {path}, "
        f"parsed {len(documented)}: {sorted(documented)}"
    )
    assert documented == DOCUMENTED_CONFIDENCE_WEIGHTS


def test_weights_that_do_not_sum_to_one_are_rejected(
    env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONFIDENCE_WEIGHT_EVIDENCE_COMPLETENESS", "0.30")

    with pytest.raises(ValidationError) as excinfo:
        Settings()  # type: ignore[call-arg]

    assert "sum to 1.0" in str(excinfo.value)


def test_llm_settings_are_required_unless_mocked(
    env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LLM_MOCK", "0")
    for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValidationError) as excinfo:
        Settings()  # type: ignore[call-arg]

    message = str(excinfo.value)
    assert "llm_base_url" in message
    assert "llm_api_key" in message
    assert "llm_model" in message


def test_llm_settings_are_optional_while_mocked(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MOCK", "1")
    for name in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings()  # type: ignore[call-arg]

    assert settings.llm_mock is True
    assert settings.llm_base_url is None


def test_boolean_flags_parse_from_strings(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CUAD_OFFLINE", "0")

    assert Settings().cuad_offline is False  # type: ignore[call-arg]


def test_database_url_psycopg_strips_the_driver_prefix(env: None) -> None:
    settings = Settings()  # type: ignore[call-arg]

    assert settings.database_url_psycopg == (
        "postgresql://rl_app:secret@localhost:5432/revenue_leakage"
    )


def test_embedding_url_is_derived_when_not_set_explicitly(
    env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:20128/v1")
    monkeypatch.delenv("EMBEDDING_URL", raising=False)

    settings = Settings()  # type: ignore[call-arg]

    assert settings.effective_embedding_url == "http://localhost:20128/api/v1/embeddings"


def test_embedding_url_override_wins(env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMBEDDING_URL", "http://example.test/embeddings")

    settings = Settings()  # type: ignore[call-arg]

    assert settings.effective_embedding_url == "http://example.test/embeddings"


def test_agent_budget_defaults_are_bounded(env: None) -> None:
    settings = Settings()  # type: ignore[call-arg]

    assert settings.agent_max_steps == 12
    assert settings.agent_max_tool_calls == 24
    assert settings.agent_token_budget == 20_000
    assert settings.agent_timeout_seconds == 120
    assert settings.agent_max_retries == 2
    assert settings.embedding_dimensions <= 2000, "pgvector cannot index wider vectors"


def test_narrative_model_falls_back_to_the_general_model(
    env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LLM_MODEL", "auto")
    monkeypatch.delenv("LLM_MODEL_NARRATIVE", raising=False)

    assert Settings().narrative_model == "auto"  # type: ignore[call-arg]


def test_only_config_reads_the_environment(env: None) -> None:
    """Acceptance criterion: no code reads os.environ outside app/config.py."""
    app_root = Path(__file__).resolve().parents[2] / "app"

    def _touches_environ(path: Path) -> bool:
        source = path.read_text(encoding="utf-8")
        return "os.environ" in source or "getenv" in source

    offenders = [
        str(path.relative_to(app_root))
        for path in app_root.rglob("*.py")
        if path.name != "config.py" and _touches_environ(path)
    ]

    assert offenders == [], f"reads os.environ outside config.py: {offenders}"
