"""
SQLAlchemy async engine and session factory.

Supports SQLite (default, file at data/jollof.db) and Postgres
(set DATABASE_URL=postgresql+asyncpg://... in .env).

Usage:
    from shared.db.engine import get_async_session, init_db

    await init_db()  # call once at startup to create tables
    async with get_async_session() as session:
        ...
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.db.models import Base
from src.config import get_settings

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine():
    global _engine
    if _engine is None:
        db_url = get_settings().database_url
        # aiosqlite driver for SQLite; asyncpg for Postgres
        if db_url.startswith("sqlite:///"):
            async_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        else:
            async_url = db_url
        _engine = create_async_engine(
            async_url,
            echo=False,
            # SQLite-specific: allow use from multiple async tasks
            connect_args={"check_same_thread": False} if "sqlite" in async_url else {},
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_factory


async def init_db() -> None:
    """Create all tables if they do not exist. Idempotent."""
    async with _get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_session_factory()
    async with factory() as session:
        yield session
