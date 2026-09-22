"""Session factory. See TICKET-004.

Plain-English: a session is one unit of work with the database. Hand one out per
request or per job, and always close it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.engine import get_engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Session factory bound to the process-wide engine."""
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def session() -> AsyncIterator[AsyncSession]:
    """Open a session, commit on success, roll back on any exception."""
    factory = get_sessionmaker()
    async with factory() as open_session:
        try:
            yield open_session
            await open_session.commit()
        except Exception:
            await open_session.rollback()
            raise
