"""Source and normalized tables. See TICKET-005.

Plain-English: mirrors of the five outside systems (Contract, CRM,
Implementation, Usage, Billing) plus the canonical customer and product rows they
resolve onto.

Two rules decide what goes in here:

1. **A source row is never corrected.** If a system told us the price was 100 and
   it was really 120, we keep 100 and record the gap later. Columns that come
   straight off the wire therefore keep the value the system sent.
2. **Source rows point at customers and products by the reference string the
   system used**, not by a foreign key. Which reference string is really which
   customer is entity resolution's job (TICKET-017); deciding it here would bake
   a guess into the schema.

Importing this package registers every table below on ``Base.metadata``, which is
what ``alembic/env.py`` needs before it can autogenerate a migration.
"""

from __future__ import annotations

from app.models.source import billing, common, contract, customer, product, subscription, usage

__all__ = ["billing", "common", "contract", "customer", "product", "subscription", "usage"]
