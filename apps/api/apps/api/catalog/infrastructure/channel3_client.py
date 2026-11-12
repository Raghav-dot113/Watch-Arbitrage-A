from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
from apps.api.catalog.application.channel3 import (
    Channel3Condition,
    Channel3NotConfiguredError,
    Channel3Product,
    Channel3SearchResponse,
    Channel3UnavailableError,
)
from pydantic import SecretStr, ValidationError

_SEARCH_URL = "https://api.trychannel3.com/v1/search"
_CHANNEL3_MAX_LIMIT = 30
_MAX_PROVIDER_PAGES = 3
_CONDITION_FILTERS: dict[Channel3Condition, list[str]] = {
    "used": ["used"],
    "new": ["new"],
    "all": ["new", "used"],
}
_ALL_AVAILABILITY_FILTERS = ["InStock", "OutOfStock"]


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
        condition: Channel3Condition = "used",
        in_stock_only: bool = False,
    ) -> Channel3SearchResponse:
        api_key = self._api_key.get_secret_value()
        if not api_key:
            raise Channel3NotConfiguredError

        products: list[Channel3Product] = []
        filtered_out_count = 0
        provider_pages_fetched = 0
        next_page_token = None
        request_page_token = page_token
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                follow_redirects=False,
                transport=self._transport,
            ) as client:
                for _ in range(_MAX_PROVIDER_PAGES):
                    payload: dict[str, Any] = {
                        "query": query,
                        "limit": min(limit, _CHANNEL3_MAX_LIMIT),
                        "filters": {
                            "conditions": _CONDITION_FILTERS[condition],
                            "availability": (
                                ["InStock"] if in_stock_only else _ALL_AVAILABILITY_FILTERS
                            ),
                        },
                    }
                    if request_page_token is not None:
                        payload["page_token"] = request_page_token

                    response = await client.post(
                        _SEARCH_URL,
                        headers={"x-api-key": api_key},
                        json=payload,
                    )
                    response.raise_for_status()
                    provider_payload = json.loads(response.content, parse_float=Decimal)
                    if not isinstance(provider_payload, dict):
                        raise Channel3UnavailableError(response.status_code)
                    provider_result = Channel3SearchResponse.model_validate(
                        {
                            **provider_payload,
                            "fetched_at": datetime.now(UTC),
                            "filtered_out_count": 0,
                            "provider_pages_fetched": 1,
                        }
                    )
                    products, page_filtered_count = filter_channel3_products(
                        provider_result.products,
                        condition=condition,
                        in_stock_only=in_stock_only,
                    )
                    filtered_out_count += page_filtered_count
                    provider_pages_fetched += 1
                    next_page_token = provider_result.next_page_token

                    if products or next_page_token is None:
                        break
                    request_page_token = next_page_token
        except httpx.HTTPStatusError as error:
            raise Channel3UnavailableError(error.response.status_code) from error
        except (
            httpx.RequestError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            ValidationError,
        ) as error:
            raise Channel3UnavailableError from error

        return Channel3SearchResponse(
            products=products[:limit],
            next_page_token=next_page_token,
            fetched_at=datetime.now(UTC),
            filtered_out_count=filtered_out_count,
            provider_pages_fetched=provider_pages_fetched,
        )


def filter_channel3_products(
    products: list[Channel3Product],
    *,
    condition: Channel3Condition,
    in_stock_only: bool = False,
) -> tuple[list[Channel3Product], int]:
    filtered_products: list[Channel3Product] = []
    filtered_out_count = 0

    for product in products:
        offers = [
            offer
            for offer in product.offers
            if (condition == "all" or offer.condition == condition)
            and (not in_stock_only or offer.availability == "InStock")
        ]
        filtered_out_count += len(product.offers) - len(offers)
        if not offers and (condition != "all" or in_stock_only):
            continue
        filtered_products.append(product.model_copy(update={"offers": offers}))

    return filtered_products, filtered_out_count
