from __future__ import annotations

from collections.abc import AsyncGenerator

from apps.api.settings import settings
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=15,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def is_dev_sqlite_database() -> bool:
    return (
        settings.environment in {"local", "test"}
        and settings.auth_mode in {"dev", "disabled"}
        and make_url(settings.database_url).get_backend_name() == "sqlite"
    )


async def initialize_database_schema() -> None:
    """Create missing tables for local SQLite and hackathon demo deployments."""
    from apps.api.infrastructure.model_registry import get_model_metadata

    async with engine.begin() as connection:
        await connection.run_sync(get_model_metadata().create_all)


async def initialize_dev_sqlite_schema() -> None:
    if not is_dev_sqlite_database():
        return
    await initialize_database_schema()


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
