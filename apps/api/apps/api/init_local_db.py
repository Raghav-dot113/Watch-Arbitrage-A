"""Initialize the local SQLite schema for development."""

from __future__ import annotations

import asyncio

from apps.api.infrastructure.database import (
    initialize_dev_sqlite_schema,
    is_dev_sqlite_database,
)


def main() -> None:
    if not is_dev_sqlite_database():
        raise SystemExit(
            "Local schema initialization requires CHRONOARB_ENVIRONMENT=local/test, "
            "CHRONOARB_AUTH_MODE=dev, and a SQLite database URL."
        )
    asyncio.run(initialize_dev_sqlite_schema())
    print("Local SQLite schema initialized.")


if __name__ == "__main__":
    main()
