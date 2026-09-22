"""Investigation state. See TICKET-006.

Plain-English: what we believe is wrong, what we looked at, what we proposed, and
what a human decided. The pipeline is the only writer, and everything here is
keyed by ``case_id``.

The split inside this package is the lifecycle: the case itself, the evidence
that supports it, the run that investigated it, and the outcome a human recorded.
"""

from __future__ import annotations

from app.models.case import (
    case,
    evidence,
    investigation,
    outcome,
)

__all__ = ["case", "evidence", "investigation", "outcome"]
