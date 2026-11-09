from __future__ import annotations

from datetime import UTC, datetime

import pytest
from apps.api.pagination import InvalidCursorError, decode_cursor, encode_cursor


def test_cursor_round_trip_is_opaque_and_preserves_order_values() -> None:
    timestamp = datetime(2026, 11, 9, 7, 10, tzinfo=UTC)
    cursor = encode_cursor(timestamp, "opp_01JTEST")

    assert "opp_01JTEST" not in cursor
    assert decode_cursor(cursor) == (timestamp, "opp_01JTEST")


@pytest.mark.parametrize("cursor", ["", "not-base64", "====", "e30"])
def test_invalid_cursor_is_rejected(cursor: str) -> None:
    with pytest.raises(InvalidCursorError):
        decode_cursor(cursor)


def test_cursor_without_timezone_is_rejected() -> None:
    import base64
    import json

    raw = json.dumps({"at": "2026-11-09T07:10:00", "id": "opp_01JTEST"}).encode()
    cursor = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    with pytest.raises(InvalidCursorError):
        decode_cursor(cursor)
