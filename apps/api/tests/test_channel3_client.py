from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
from apps.api.catalog.application.channel3 import (
    Channel3NotConfiguredError,
    Channel3UnavailableError,
)
from apps.api.catalog.infrastructure.channel3_client import Channel3Client
from pydantic import SecretStr


async def test_channel3_search_sends_secret_query_and_parses_prices_as_decimal() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == "https://api.trychannel3.com/v1/search"
        assert request.headers["x-api-key"] == "channel3-test-key"
        assert request.read() == (
            b'{"query":"Rolex Submariner","limit":10,"page_token":"next-page"}'
        )
        return httpx.Response(
            200,
            content=(
                b'{"products":[{"id":"product-1","title":"Submariner","offers":['
                b'{"url":"https://retailer.example/watch","domain":"retailer.example",'
                b'"price":{"amount":12950.50,"currency":"USD"},'
                b'"availability":"InStock","condition":"used"}]}],'
                b'"next_page_token":null}'
            ),
            request=request,
        )

    client = Channel3Client(
        SecretStr("channel3-test-key"),
        3,
        transport=httpx.MockTransport(handle),
    )
    result = await client.search(
        query="Rolex Submariner",
        limit=10,
        page_token="next-page",
    )

    assert result.products[0].title == "Submariner"
    assert result.products[0].offers[0].price.amount == Decimal("12950.50")
    assert result.products[0].offers[0].condition == "used"
    assert result.fetched_at.tzinfo is not None


async def test_channel3_search_requires_configured_key() -> None:
    client = Channel3Client(SecretStr(""), 3)

    with pytest.raises(Channel3NotConfiguredError):
        await client.search(query="Rolex", limit=20, page_token=None)


async def test_channel3_search_surfaces_provider_status_without_provider_body() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={"detail": "provider-specific response"},
            request=request,
        )

    client = Channel3Client(
        SecretStr("channel3-test-key"),
        3,
        transport=httpx.MockTransport(handle),
    )

    with pytest.raises(Channel3UnavailableError) as error:
        await client.search(query="Rolex", limit=20, page_token=None)

    assert error.value.status_code == 429
    assert "provider-specific response" not in str(error.value)
