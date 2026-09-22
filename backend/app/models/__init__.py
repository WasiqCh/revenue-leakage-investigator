"""Table definitions. See TICKET-005.

Plain-English: this package is split the same way ``docs/data-model.md`` splits
the data -- ``source`` (what the outside systems reported), ``derived`` (what our
code computed), ``case`` (investigation state) and ``ops`` (infrastructure).

Alembic's ``env.py`` imports these packages for their side effect: importing a
model registers its table on ``Base.metadata``, which is what autogenerate
compares the database against. Importing them here too means any code that
touches the models gets a complete metadata object.
"""

from __future__ import annotations

from app.models import case, derived, ops, source

__all__ = ["case", "derived", "ops", "source"]
