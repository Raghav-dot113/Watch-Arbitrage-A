from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Query

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


class InvalidCursorError(ValueError):
    pass


@dataclass(frozen=True)
class PaginationParams:
    limit: int
    cursor: str | None


@dataclass(frozen=True)
class Page[ItemT]:
    items: list[ItemT]
    next_cursor: str | None
    has_more: bool


def pagination_params(
    limit: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    cursor: str | None = Query(default=None, max_length=1024),
) -> PaginationParams:
    return PaginationParams(limit=limit, cursor=cursor)


def encode_cursor(timestamp: datetime, item_id: str) -> str:
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    payload = json.dumps(
        {"at": timestamp.isoformat(), "id": item_id},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        if not cursor or len(cursor) > 1024:
            raise ValueError
        padding = "=" * (-len(cursor) % 4)
        raw_cursor = base64.b64decode(
            (cursor + padding).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
        payload = json.loads(raw_cursor.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError
        timestamp_value = payload.get("at", payload.get("published_at"))
        item_id = payload.get("id")
        if not isinstance(timestamp_value, str) or not isinstance(item_id, str) or not item_id:
            raise ValueError
        timestamp = datetime.fromisoformat(timestamp_value)
        if timestamp.tzinfo is None:
            raise ValueError
        return timestamp, item_id
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error):
        raise InvalidCursorError("The cursor is invalid.") from None
