from __future__ import annotations

from pathlib import Path

import pytest
from apps.api.infrastructure import database
from apps.api.settings import PROJECT_ROOT, Settings, settings
from sqlalchemy import inspect
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine


def test_relative_sqlite_url_resolves_from_project_root() -> None:
    configured = Settings(
        _env_file=None,
        environment="local",
        auth_mode="dev",
        database_url="sqlite+aiosqlite:///chronoarb.db",
    )

    assert Path(PROJECT_ROOT / "chronoarb.db").is_absolute()
    assert make_url(configured.database_url).database == str(PROJECT_ROOT / "chronoarb.db")


async def test_local_sqlite_initializer_creates_identity_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_async_engine("sqlite+aiosqlite://")
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "auth_mode", "dev")
    monkeypatch.setattr(database, "engine", engine)

    try:
        await database.initialize_dev_sqlite_schema()
        async with engine.connect() as connection:
            table_names = await connection.run_sync(
                lambda sync_connection: inspect(sync_connection).get_table_names()
            )
        assert {"users", "organizations", "memberships"}.issubset(table_names)
    finally:
        await engine.dispose()
