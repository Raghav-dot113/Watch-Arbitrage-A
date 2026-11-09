from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
from typing import NamedTuple

from chronoarb.domain.errors import ValidationError

_CURSOR_FIELDS = frozenset({"sort_key", "sort_value", "id", "checksum"})
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class Cursor(NamedTuple):
    sort_key: str
    sort_value: str
    id: str


def _cursor_payload(sort_key: str, sort_value: str, id: str) -> bytes:
    return json.dumps(
        {"sort_key": sort_key, "sort_value": sort_value, "id": id},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def encode_cursor(sort_key: str, sort_value: str, id: str) -> str:
    if not all(isinstance(value, str) and value for value in (sort_key, id)):
        raise ValidationError("Cursor sort key and id must be non-empty strings")
    if not isinstance(sort_value, str):
        raise ValidationError("Cursor sort value must be a string")

    payload = _cursor_payload(sort_key, sort_value, id)
    encoded = json.loads(payload)
    encoded["checksum"] = hashlib.sha256(payload).hexdigest()
    token = json.dumps(encoded, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
        "ascii"
    )
    return base64.urlsafe_b64encode(token).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> Cursor:
    if not isinstance(cursor, str) or not cursor:
        raise ValidationError("Cursor must be a non-empty base64url string")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", cursor):
        raise ValidationError("Cursor contains invalid base64url characters")

    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        token = base64.b64decode(padded, altchars=b"-_", validate=True)
        decoded = json.loads(token)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError("Cursor is malformed") from error

    if not isinstance(decoded, dict) or set(decoded) != _CURSOR_FIELDS:
        raise ValidationError("Cursor has an invalid shape")
    sort_key = decoded["sort_key"]
    sort_value = decoded["sort_value"]
    id = decoded["id"]
    checksum = decoded["checksum"]
    if not all(isinstance(value, str) for value in (sort_key, sort_value, id, checksum)):
        raise ValidationError("Cursor fields must be strings")
    if not sort_key or not id or not _SHA256_HEX.fullmatch(checksum):
        raise ValidationError("Cursor fields are invalid")

    expected_checksum = hashlib.sha256(_cursor_payload(sort_key, sort_value, id)).hexdigest()
    if not hmac.compare_digest(checksum, expected_checksum):
        raise ValidationError("Cursor checksum does not match")
    return Cursor(sort_key, sort_value, id)
