"""Typed settings for the whole application. See TICKET-003.

Plain-English: every knob in the system lives here, with a clear name and a
documented default. Nothing else in the codebase is allowed to read
``os.environ`` -- if you need a setting, import it from this module.

Where the values come from:
    The process environment only. ``docker-compose.yml`` injects them into the
    backend and worker containers (substituting from the root ``.env``). No
    ``.env`` file is read at runtime: if something important is missing the app
    refuses to start and names the field, rather than silently guessing.

Fail-fast rules:
    * ``DATABASE_URL`` is always required.
    * The LLM settings are required unless ``LLM_MOCK`` is on (tests run offline).
    * The eight confidence weights must sum to exactly 1.0.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from functools import lru_cache
from typing import Final

from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The published confidence weights live in docs/confidence.md. They are copied
# here so a test can assert the defaults still match the documentation.
DOCUMENTED_CONFIDENCE_WEIGHTS: Final[dict[str, Decimal]] = {
    "evidence_completeness": Decimal("0.25"),
    "source_agreement": Decimal("0.20"),
    "deterministic_certainty": Decimal("0.15"),
    "contract_clarity": Decimal("0.10"),
    "exception_absence": Decimal("0.10"),
    "data_freshness": Decimal("0.08"),
    "historical_precedent": Decimal("0.07"),
    "amount_materiality": Decimal("0.05"),
}

# Tolerances as published in docs/billing-periods.md.
DOCUMENTED_MONEY_TOLERANCE_ABS: Final[Decimal] = Decimal("1.00")
DOCUMENTED_MONEY_TOLERANCE_PCT: Final[Decimal] = Decimal("0.005")

# SQLAlchemy needs the driver in the URL; psycopg itself does not understand it.
SQLALCHEMY_DRIVER_PREFIX: Final[str] = "postgresql+psycopg://"


class Settings(BaseSettings):
    """Every configurable value in the system.

    Field names map to environment variables one-to-one, upper-cased. For
    example ``money_tolerance_abs`` is read from ``MONEY_TOLERANCE_ABS``.
    """

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )

    # --- Database -----------------------------------------------------------
    database_url: str = Field(
        ...,
        description="SQLAlchemy DSN, e.g. postgresql+psycopg://user:pass@host:5432/db",
    )

    # --- LLM provider (OpenAI-compatible) -----------------------------------
    llm_base_url: str | None = Field(
        default=None,
        description="OpenAI-compatible endpoint, e.g. http://localhost:20128/v1",
    )
    llm_api_key: str | None = Field(
        default=None,
        description="API key for the LLM endpoint.",
    )
    llm_model: str | None = Field(
        default=None,
        description="Model used for structured reads.",
    )
    llm_model_narrative: str | None = Field(
        default=None,
        description="Model used for narrative writing. Falls back to llm_model.",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Embedding model id. Some gateways need an 'openrouter/' prefix.",
    )
    embedding_dimensions: int = Field(
        default=1536,
        description=(
            "Embedding width. Must stay <= 2000: pgvector cannot index wider "
            "vectors, and some gateways default to 3072/4096 unless asked."
        ),
    )
    embedding_url: str | None = Field(
        default=None,
        description=(
            "Full embeddings endpoint. Leave unset to derive it from "
            "llm_base_url (many gateways serve it at /api/v1/embeddings)."
        ),
    )

    # --- Offline / test mode ------------------------------------------------
    llm_mock: bool = Field(
        default=False,
        description="When true, no network calls are made. Tests always run with this on.",
    )
    cuad_offline: bool = Field(
        default=True,
        description="When true, the CUAD dataset is never downloaded.",
    )

    # --- CUAD real-data fetch -----------------------------------------------
    cuad_zenodo_url: str = Field(
        default="https://zenodo.org/records/4595826/files/CUAD_v1.zip?download=1",
        description="Public contract dataset used for realistic testing (ADR-007).",
    )
    cuad_zenodo_md5: str = Field(
        default="c38f490a984420b8a62600db401fafd5",
        description="Checksum of the CUAD archive.",
    )
    cuad_max_contracts: int = Field(
        default=100,
        description="How many contracts to keep from the archive.",
    )
    cuad_cache_dir: str = Field(
        default="data/cuad",
        description="Where downloads are cached. Never committed.",
    )

    # --- Cloudflare AI Search (optional comparison baseline, ADR-009) -------
    cf_account_id: str | None = Field(default=None, description="Optional.")
    cf_ai_search_instance_id: str | None = Field(default=None, description="Optional.")
    cf_api_token: str | None = Field(default=None, description="Optional.")

    # --- Detection tuning ---------------------------------------------------
    confidence_high_threshold: int = Field(
        default=90, description="Score at or above this is auto-confirmed."
    )
    confidence_medium_threshold: int = Field(
        default=75, description="Score at or above this is NEEDS_REVIEW."
    )
    money_tolerance_abs: Decimal = Field(
        default=DOCUMENTED_MONEY_TOLERANCE_ABS,
        description="Ignore money differences smaller than this many currency units.",
    )
    money_tolerance_pct: Decimal = Field(
        default=DOCUMENTED_MONEY_TOLERANCE_PCT,
        description=(
            "Ignore relative differences smaller than this fraction (0.005 == 0.5 percent)."
        ),
    )

    # --- Confidence weights (docs/confidence.md) ----------------------------
    confidence_weight_evidence_completeness: Decimal = Field(
        default=DOCUMENTED_CONFIDENCE_WEIGHTS["evidence_completeness"]
    )
    confidence_weight_source_agreement: Decimal = Field(
        default=DOCUMENTED_CONFIDENCE_WEIGHTS["source_agreement"]
    )
    confidence_weight_deterministic_certainty: Decimal = Field(
        default=DOCUMENTED_CONFIDENCE_WEIGHTS["deterministic_certainty"]
    )
    confidence_weight_contract_clarity: Decimal = Field(
        default=DOCUMENTED_CONFIDENCE_WEIGHTS["contract_clarity"]
    )
    confidence_weight_exception_absence: Decimal = Field(
        default=DOCUMENTED_CONFIDENCE_WEIGHTS["exception_absence"]
    )
    confidence_weight_data_freshness: Decimal = Field(
        default=DOCUMENTED_CONFIDENCE_WEIGHTS["data_freshness"]
    )
    confidence_weight_historical_precedent: Decimal = Field(
        default=DOCUMENTED_CONFIDENCE_WEIGHTS["historical_precedent"]
    )
    confidence_weight_amount_materiality: Decimal = Field(
        default=DOCUMENTED_CONFIDENCE_WEIGHTS["amount_materiality"]
    )

    # --- Agent budgets ------------------------------------------------------
    agent_max_steps: int = Field(
        default=12, description="Reasoning steps allowed per investigation."
    )
    agent_max_tool_calls: int = Field(
        default=24, description="Tool calls allowed per investigation."
    )
    agent_token_budget: int = Field(default=20_000, description="Tokens allowed per investigation.")
    agent_timeout_seconds: int = Field(
        default=120, description="Wall-clock limit per investigation."
    )
    agent_max_retries: int = Field(
        default=2,
        description=(
            "Retries for a failed provider call. Retries back off; the gateway "
            "we use returns HTTP 502 when its free pool is exhausted."
        ),
    )

    # --- Reporting ----------------------------------------------------------
    reporting_currency: str = Field(default="USD", description="ISO-4217 code.")
    default_as_of_date: date = Field(
        default=date(2026, 8, 31),
        description=(
            "Fallback as-of date. Money and period code always takes an "
            "as_of_date argument rather than calling datetime.now() (AGENTS.md 1.4)."
        ),
    )

    @model_validator(mode="after")
    def _require_llm_settings_unless_mocked(self) -> Settings:
        """Fail fast, naming the field, instead of guessing at runtime."""
        if self.llm_mock:
            return self
        missing = [
            name for name in ("llm_base_url", "llm_api_key", "llm_model") if not getattr(self, name)
        ]
        if missing:
            raise ValueError(
                "missing required settings while LLM_MOCK is off: " + ", ".join(missing)
            )
        return self

    @model_validator(mode="after")
    def _confidence_weights_must_sum_to_one(self) -> Settings:
        total = sum(
            (
                self.confidence_weight_evidence_completeness,
                self.confidence_weight_source_agreement,
                self.confidence_weight_deterministic_certainty,
                self.confidence_weight_contract_clarity,
                self.confidence_weight_exception_absence,
                self.confidence_weight_data_freshness,
                self.confidence_weight_historical_precedent,
                self.confidence_weight_amount_materiality,
            ),
            Decimal(0),
        )
        if total != Decimal(1):
            raise ValueError(
                f"confidence weights must sum to 1.0, got {total} (see docs/confidence.md)"
            )
        return self

    @property
    def database_url_psycopg(self) -> str:
        """The DSN with the SQLAlchemy driver prefix removed.

        Plain psycopg (used by the worker healthcheck and by tests) cannot
        parse ``postgresql+psycopg://``.
        """
        if self.database_url.startswith(SQLALCHEMY_DRIVER_PREFIX):
            return "postgresql://" + self.database_url[len(SQLALCHEMY_DRIVER_PREFIX) :]
        return self.database_url

    @property
    def effective_embedding_url(self) -> str:
        """Embeddings endpoint: explicit if set, otherwise derived.

        The gateway we develop against serves chat at ``/v1`` and embeddings at
        ``/api/v1/embeddings``, so the derivation swaps the suffix.
        """
        if self.embedding_url:
            return self.embedding_url
        base = (self.llm_base_url or "").rstrip("/")
        base = base.removesuffix("/v1")
        return base + "/api/v1/embeddings"

    @property
    def narrative_model(self) -> str | None:
        """Narrative model, falling back to the general model."""
        return self.llm_model_narrative or self.llm_model


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings object (built once)."""
    return Settings()  # type: ignore[call-arg]


def settings_or_none() -> Settings | None:
    """Return the settings, or None when the environment is not configured.

    Plain-English: this module is the only place allowed to look at environment
    variables, and the tier-1 verifier enforces that on every file in the repo.
    Tests that need to know "is there actually a database to talk to" ask this
    function instead of reading ``os.environ`` themselves -- otherwise they skip
    quietly on a developer machine and the gate goes red.
    """
    try:
        return get_settings()
    except (ValidationError, ValueError):
        return None
