"""Tables our own code computes, never a system reports. See TICKET-006.

Plain-English: everything in here can be deleted and rebuilt by re-running the
pipeline. That is the point -- a derived row is an answer we calculated, so if
the calculation changes, the row is regenerated rather than edited.

Upserting on the natural key is what makes that safe: re-running detection
recomputes the same key and writes zero new rows (AGENTS.md 1.4).
"""

from __future__ import annotations

from app.models.derived import (
    billing_period,
    entity_resolution,
    reconciliation_result,
)

__all__ = ["billing_period", "entity_resolution", "reconciliation_result"]
