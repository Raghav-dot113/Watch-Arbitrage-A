from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JobEnvelope:
    trace_id: str
    stage: str
    payload: dict[str, Any]
    idempotency_key: str
    attempt: int = 0
    max_attempts: int = 5

    def __post_init__(self) -> None:
        if not self.trace_id.startswith("trc_"):
            raise ValueError("trace_id must use the trc_ namespace")
        if self.attempt < 0 or self.max_attempts < 1:
            raise ValueError("attempt and max_attempts are invalid")
        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a dictionary")
        if not self.idempotency_key:
            raise ValueError("idempotency_key is required")

    def next_attempt(self) -> JobEnvelope:
        if self.attempt >= self.max_attempts - 1:
            raise RuntimeError("Job has exhausted bounded retries")
        return JobEnvelope(
            trace_id=self.trace_id,
            stage=self.stage,
            payload=self.payload,
            idempotency_key=self.idempotency_key,
            attempt=self.attempt + 1,
            max_attempts=self.max_attempts,
        )


def make_idempotency_key(stage: str, payload: dict[str, Any], version: str) -> str:
    canonical = json.dumps(
        {"stage": stage, "payload": payload, "version": version},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()
