from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Annotated, Any

from apps.api.infrastructure.http_status import HTTP_422_UNPROCESSABLE_ENTITY
from fastapi import Header, HTTPException

_IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[\x21-\x7e]{1,255}$")


@dataclass(frozen=True)
class IdempotencyIdentity:
    storage_key: str
    request_fingerprint: str


async def require_idempotency_key(
    value: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> str:
    if value is None:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Idempotency-Key header is required",
        )
    return validate_idempotency_key(value)


def validate_idempotency_key(value: str) -> str:
    if not _IDEMPOTENCY_KEY_PATTERN.fullmatch(value):
        raise ValueError(
            "Idempotency-Key must contain 1 to 255 printable ASCII characters without spaces"
        )
    return value


def make_idempotency_identity(
    *,
    key: str,
    organization_id: str,
    user_id: str,
    operation: str,
    payload: dict[str, Any],
) -> IdempotencyIdentity:
    """Derive globally unique storage material and a stable request fingerprint."""
    validate_idempotency_key(key)
    for label, value in (
        ("organization_id", organization_id),
        ("user_id", user_id),
        ("operation", operation),
    ):
        if not value.strip():
            raise ValueError(f"{label} must not be empty")

    scope = json.dumps(
        [organization_id, user_id, operation, key],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    canonical_payload = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return IdempotencyIdentity(
        storage_key=f"idem_{hashlib.sha256(scope).hexdigest()}",
        request_fingerprint=hashlib.sha256(canonical_payload).hexdigest(),
    )
