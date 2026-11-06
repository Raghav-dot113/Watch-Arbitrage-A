from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from chronoarb.domain.source_adapters.protocol import (
    HealthIssue,
    ParsedBatch,
    ParsedListing,
    RawObservation,
    SourceItemRef,
    SourceScope,
)


@dataclass(frozen=True)
class FixtureScope:
    records: tuple[dict[str, Any], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple):
            raise TypeError("FixtureScope.records must be a tuple")


@dataclass(frozen=True)
class FixtureObservation:
    payload: dict[str, Any]
    fetched_at: datetime


@dataclass(frozen=True)
class FixtureParsedListing:
    external_id: str
    title: str
    price: str | None
    currency: str | None
    listed_at: datetime | None
    attributes: dict[str, Any]


@dataclass(frozen=True)
class FixtureBatch:
    listings: tuple[FixtureParsedListing, ...]


@dataclass(frozen=True)
class FixtureHealthIssue:
    code: str
    message: str


class FixtureAdapter:
    source_key = "fixture"
    adapter_version = "fixture-v1"
    access_mode = "fixture"
    approval_ref = "offline-test-fixture"

    async def discover(self, scope: SourceScope) -> AsyncIterator[SourceItemRef]:
        if not isinstance(scope, FixtureScope):
            raise TypeError("FixtureAdapter requires FixtureScope")
        for index, record in enumerate(scope.records):
            external_id = str(record.get("external_id") or f"fixture-{index}")
            yield SourceItemRef(source_key=self.source_key, external_id=external_id)

    async def fetch(self, item: SourceItemRef) -> RawObservation:
        return FixtureObservation(
            payload={"external_id": item.external_id},
            fetched_at=datetime.now(UTC),
        )

    def parse(self, raw: RawObservation) -> ParsedListing:
        if not isinstance(raw, FixtureObservation):
            raise TypeError("FixtureAdapter requires FixtureObservation")
        payload = raw.payload
        return FixtureParsedListing(
            external_id=str(payload["external_id"]),
            title=str(payload.get("title") or payload["external_id"]),
            price=str(payload["price"]) if payload.get("price") is not None else None,
            currency=str(payload["currency"]).upper() if payload.get("currency") else None,
            listed_at=None,
            attributes=dict(payload.get("attributes") or {}),
        )

    def stable_external_id(self, parsed: ParsedListing) -> str:
        if not isinstance(parsed, FixtureParsedListing):
            raise TypeError("FixtureAdapter requires FixtureParsedListing")
        return parsed.external_id

    def health_assertions(self, batch: ParsedBatch) -> list[HealthIssue]:
        if not isinstance(batch, FixtureBatch):
            raise TypeError("FixtureAdapter requires FixtureBatch")
        issues: list[HealthIssue] = []
        if not batch.listings:
            issues.append(FixtureHealthIssue("EMPTY_BATCH", "Fixture batch contains no listings"))
        return issues


def fixture_checksum(payload: dict[str, Any]) -> str:
    import json

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()
