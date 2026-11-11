from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
from apps.api.catalog.application.channel3 import (
    Channel3NotConfiguredError,
    Channel3SearchResponse,
    Channel3UnavailableError,
)
from pydantic import SecretStr, ValidationError

_SEARCH_URL = "https://api.trychannel3.com/v1/search"


class Channel3Client:
    def __init__(
        self,
        api_key: SecretStr,
        timeout_seconds: float,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def search(
        self,
        *,
        query: str,
        limit: int,
        page_token: str | None,
    ) -> Channel3SearchResponse:
        api_key = self._api_key.get_secret_value()
        if not api_key:
            raise Channel3NotConfiguredError

        payload: dict[str, Any] = {"query": query, "limit": limit}
        if page_token is not None:
            payload["page_token"] = page_token

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                follow_redirects=False,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    _SEARCH_URL,
                    headers={"x-api-key": api_key},
                    json=payload,
                )
            response.raise_for_status()
            provider_payload = json.loads(response.content, parse_float=Decimal)
            if not isinstance(provider_payload, dict):
                raise Channel3UnavailableError
            result = Channel3SearchResponse.model_validate(
                {**provider_payload, "fetched_at": datetime.now(UTC)}
            )
        except httpx.HTTPStatusError as error:
            raise Channel3UnavailableError(error.response.status_code) from error
        except (
            httpx.RequestError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            ValidationError,
        ) as error:
            raise Channel3UnavailableError from error

        return result
