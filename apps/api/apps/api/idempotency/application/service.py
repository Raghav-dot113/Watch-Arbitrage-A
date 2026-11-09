from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from apps.api.idempotency.infrastructure.models import IdempotencyRecord
from apps.api.idempotency.infrastructure.repositories import IdempotencyRepository
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from chronoarb.domain.ulid import generate_ulid


class IdempotencyKeyReuseError(Exception):
    pass


@dataclass(frozen=True)
class IdempotencyResult:
    status_code: int
    response_body: dict[str, Any]
    replayed: bool


class IdempotencyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._records = IdempotencyRepository(session)

    @staticmethod
    def request_hash(request_body: dict[str, Any]) -> str:
        canonical_body = json.dumps(
            request_body,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return hashlib.sha256(canonical_body).hexdigest()

    @staticmethod
    def scoped_key(organization_id: str, route_key: str, key: str) -> str:
        value = f"{organization_id}\0{route_key}\0{key}".encode()
        return hashlib.sha256(value).hexdigest()

    async def execute(
        self,
        *,
        organization_id: str,
        route_key: str,
        key: str,
        request_body: dict[str, Any],
        operation: Callable[[], Awaitable[tuple[int, dict[str, Any]]]],
    ) -> IdempotencyResult:
        body_hash = self.request_hash(request_body)
        existing = await self._records.get(organization_id, route_key, key)
        if existing is not None:
            return self._replay(existing, body_hash)

        try:
            status_code, response_body = await operation()
            await self._records.save(
                IdempotencyRecord(
                    id=generate_ulid("idm"),
                    organization_id=organization_id,
                    route_key=route_key,
                    idempotency_key=key,
                    request_hash=body_hash,
                    response_status=status_code,
                    response_body=response_body,
                )
            )
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            concurrent_record = await self._records.get(organization_id, route_key, key)
            if concurrent_record is None:
                raise
            return self._replay(concurrent_record, body_hash)
        except Exception:
            await self._session.rollback()
            raise

        return IdempotencyResult(status_code, response_body, replayed=False)

    @staticmethod
    def _replay(record: IdempotencyRecord, body_hash: str) -> IdempotencyResult:
        if record.request_hash != body_hash:
            raise IdempotencyKeyReuseError
        return IdempotencyResult(200, record.response_body, replayed=True)
