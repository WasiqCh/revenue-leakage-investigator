"""Enumerations shared by the schema and the application. See TICKET-004.

Plain-English: the fixed lists of values that appear in columns. Keeping them in
one place means the database and the code can never disagree about spelling.

These are ``StrEnum``s, so the value stored in Postgres is the readable string
rather than an opaque integer.
"""

from __future__ import annotations

from enum import StrEnum


class SourceSystem(StrEnum):
    """The five outside systems we reconcile."""

    CONTRACT = "contract"
    CRM = "crm"
    IMPLEMENTATION = "implementation"
    USAGE = "usage"
    BILLING = "billing"


class CaseStatus(StrEnum):
    """Lifecycle of an investigated discrepancy."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    VALID_EXCEPTION = "valid_exception"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ConfidenceBand(StrEnum):
    """Band assigned after the weighted score (docs/confidence.md)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class JobStatus(StrEnum):
    """Bookkeeping for background work."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
