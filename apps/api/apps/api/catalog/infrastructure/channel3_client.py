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
_CHANNEL3_MAX_LIMIT = 30


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

        payload: dict[str, Any] = {"query": query, "limit": min(limit, _CHANNEL3_MAX_LIMIT)}
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
                raise Channel3UnavailableError(
                    response.status_code,
                    code="invalid_provider_response",
                    message="Search provider returned an invalid response.",
                    retryable=False,
                )
            result = Channel3SearchResponse.model_validate(
                {
                    **_map_provider_payload(provider_payload, response.status_code),
                    "fetched_at": datetime.now(UTC),
                }
            )
        except httpx.HTTPStatusError as error:
            raise _provider_status_error(error.response.status_code) from error
        except httpx.TimeoutException as error:
            raise Channel3UnavailableError(
                code="provider_timeout",
                message="Search provider timed out. Try again shortly.",
            ) from error
        except httpx.RequestError as error:
            raise Channel3UnavailableError(
                code="provider_network_error",
                message="Search provider could not be reached. Try again shortly.",
            ) from error
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            raise Channel3UnavailableError(
                response.status_code,
                code="invalid_provider_response",
                message="Search provider returned an invalid response.",
                retryable=False,
            ) from error

        return result.model_copy(update={"products": result.products[:limit]})


def _map_provider_payload(payload: dict[str, Any], status_code: int) -> dict[str, Any]:
    products = payload.get("products")
    if not isinstance(products, list):
        raise Channel3UnavailableError(
            status_code,
            code="invalid_provider_response",
            message="Search provider returned an invalid response.",
            retryable=False,
        )

    mapped_products: list[Any] = []
    for product in products:
        if not isinstance(product, dict):
            mapped_products.append(product)
            continue

        mapped_product = dict(product)
        for field in ("brands", "images", "offers"):
            if mapped_product.get(field) is None:
                mapped_product[field] = []

        offers = mapped_product.get("offers")
        if isinstance(offers, list):
            mapped_offers: list[Any] = []
            for offer in offers:
                if not isinstance(offer, dict):
                    mapped_offers.append(offer)
                    continue
                mapped_offer = dict(offer)
                price = mapped_offer.get("price")
                if isinstance(price, dict) and "price" in price:
                    mapped_offer["price"] = {
                        "amount": price["price"],
                        "currency": price.get("currency"),
                        "compare_at_price": price.get("compare_at_price"),
                    }
                elif price is None:
                    mapped_offer["price"] = None
                mapped_offers.append(mapped_offer)
            mapped_product["offers"] = mapped_offers
        mapped_products.append(mapped_product)

    return {**payload, "products": mapped_products}


def _provider_status_error(status_code: int) -> Channel3UnavailableError:
    if status_code == 401:
        return Channel3UnavailableError(
            status_code,
            code="invalid_key",
            message="The search provider key is invalid. Contact your administrator.",
            retryable=False,
        )
    if status_code == 402:
        return Channel3UnavailableError(
            status_code,
            code="credits_exhausted",
            message="Search credits are exhausted. Contact your administrator.",
            retryable=False,
        )
    if status_code == 429:
        return Channel3UnavailableError(
            status_code,
            code="rate_limited",
            message="The search provider is rate limited. Try again shortly.",
        )
    if status_code >= 500:
        return Channel3UnavailableError(
            status_code,
            code="provider_unavailable",
            message="Search provider is temporarily unavailable. Try again shortly.",
        )
    return Channel3UnavailableError(
        status_code,
        code="provider_rejected_request",
        message="Search provider rejected the request.",
        retryable=False,
    )
