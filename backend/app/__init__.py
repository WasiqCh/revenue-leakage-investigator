"""Application package for the revenue leakage investigator.

TICKET-001 creates this package so that the tooling contract is verifiable:
the ticket's acceptance criteria require ``mypy`` to report zero errors on
``app/``, and mypy exits 2 when the target directory does not exist. Later
tickets fill this package with the real modules.
"""
