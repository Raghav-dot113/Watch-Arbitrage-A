from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from apps.api.catalog.application.channel3 import (
    Channel3NotConfiguredError,
    Channel3UnavailableError,
)
from apps.api.catalog.infrastructure.channel3_client import Channel3Client
from pydantic import SecretStr

_SEARCH_FIXTURE = Path(__file__).parent / "fixtures" / "channel3_search.json"


async def test_channel3_search_sends_secret_query_and_parses_prices_as_decimal() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == "https://api.trychannel3.com/v1/search"
        assert request.headers["x-api-key"] == "channel3-test-key"
        assert request.read() == (
            b'{"query":"Rolex Submariner","limit":10,"page_token":"next-page"}'
        )
        return httpx.Response(200, content=_SEARCH_FIXTURE.read_bytes(), request=request)

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

    assert result.products[0].title == "Submariner Date"
    assert result.products[0].offers[0].price.amount == Decimal("12950.50")
    assert result.products[0].offers[0].price.compare_at_price == Decimal("15000")
    assert result.products[0].offers[0].condition == "used"
    assert result.products[1].brands == []
    assert result.products[1].images == []
    assert result.products[1].offers == []
    assert result.fetched_at.tzinfo is not None
    fixture = json.loads(_SEARCH_FIXTURE.read_text(encoding="utf-8"))
    assert "amount" not in fixture["products"][0]["offers"][0]["price"]


async def test_channel3_search_caps_provider_limit_at_documented_maximum() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.read())["limit"] == 30
        return httpx.Response(
            200,
            json={"products": [], "next_page_token": None},
            request=request,
        )

    client = Channel3Client(
        SecretStr("channel3-test-key"),
        3,
        transport=httpx.MockTransport(handle),
    )

    await client.search(query="Rolex", limit=50, page_token=None)


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
    assert error.value.code == "rate_limited"
    assert error.value.retryable is True
    assert "provider-specific response" not in str(error.value)


@pytest.mark.parametrize(
    ("status_code", "code", "message", "retryable"),
    [
        (401, "invalid_key", "key is invalid", False),
        (402, "credits_exhausted", "credits are exhausted", False),
        (429, "rate_limited", "rate limited", True),
    ],
)
async def test_channel3_provider_statuses_have_safe_distinct_errors(
    status_code: int,
    code: str,
    message: str,
    retryable: bool,
) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
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

    assert error.value.status_code == status_code
    assert error.value.code == code
    assert message in error.value.message
    assert error.value.retryable is retryable
    assert "provider-specific response" not in str(error.value)


@pytest.mark.parametrize(
    ("failure", "code"),
    [
        (httpx.TimeoutException("private timeout detail"), "provider_timeout"),
        (httpx.ConnectError("private network detail"), "provider_network_error"),
    ],
)
async def test_channel3_network_failures_have_safe_distinct_errors(
    failure: httpx.RequestError,
    code: str,
) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        raise failure

    client = Channel3Client(
        SecretStr("channel3-test-key"),
        3,
        transport=httpx.MockTransport(handle),
    )

    with pytest.raises(Channel3UnavailableError) as error:
        await client.search(query="Rolex", limit=20, page_token=None)

    assert error.value.code == code
    assert error.value.retryable is True
    assert "private" not in str(error.value)


async def test_channel3_invalid_provider_response_is_classified_without_body() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"products": "invalid provider data"},
            request=request,
        )

    client = Channel3Client(
        SecretStr("channel3-test-key"),
        3,
        transport=httpx.MockTransport(handle),
    )

    with pytest.raises(Channel3UnavailableError) as error:
        await client.search(query="Rolex", limit=20, page_token=None)

    assert error.value.status_code == 200
    assert error.value.code == "invalid_provider_response"
    assert error.value.retryable is False
    assert "invalid provider data" not in str(error.value)
