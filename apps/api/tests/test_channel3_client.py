from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from apps.api.catalog.api.schemas import Channel3SearchRequest
from apps.api.catalog.application.channel3 import (
    Channel3NotConfiguredError,
    Channel3Offer,
    Channel3Price,
    Channel3Product,
    Channel3UnavailableError,
)
from apps.api.catalog.infrastructure.channel3_client import (
    Channel3Client,
    filter_channel3_products,
)
from pydantic import SecretStr

_SEARCH_FIXTURE = Path(__file__).parent / "fixtures" / "channel3_search.json"


async def test_channel3_search_sends_filters_and_preserves_decimal_prices() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert str(request.url) == "https://api.trychannel3.com/v1/search"
        assert request.headers["x-api-key"] == "channel3-test-key"
        assert json.loads(request.read()) == {
            "query": "Rolex Submariner",
            "limit": 10,
            "filters": {
                "conditions": ["new", "used"],
                "availability": ["InStock", "OutOfStock"],
            },
            "page_token": "next-page",
        }
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
        condition="all",
    )

    assert result.products[0].title == "Submariner Date"
    assert result.products[0].offers[0].price.amount == Decimal("12950.5")
    assert result.products[0].offers[0].price.compare_at_price == Decimal("15000")
    assert result.products[0].offers[0].condition == "used"
    assert result.products[1].offers == []
    assert result.filtered_out_count == 0
    assert result.provider_pages_fetched == 1
    assert result.fetched_at.tzinfo is not None
    fixture = json.loads(_SEARCH_FIXTURE.read_text(encoding="utf-8"))
    assert "amount" not in fixture["products"][0]["offers"][0]["price"]


async def test_channel3_search_caps_limit_and_sends_stock_filter() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.read())
        assert payload["limit"] == 30
        assert payload["filters"] == {
            "conditions": ["used"],
            "availability": ["InStock"],
        }
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

    await client.search(
        query="Rolex",
        limit=50,
        page_token=None,
        in_stock_only=True,
    )


def _offer(condition: str | None, availability: str = "InStock") -> Channel3Offer:
    return Channel3Offer(
        url=f"https://retailer.example/{condition or 'unknown'}",
        domain="retailer.example",
        price=Channel3Price(amount=Decimal("1000"), currency="USD"),
        availability=availability,
        condition=condition,
    )


def _product(*offers: Channel3Offer) -> Channel3Product:
    return Channel3Product(id="watch", title="Watch", offers=list(offers))


def test_search_request_defaults_to_used_and_rejects_unknown_conditions() -> None:
    request = Channel3SearchRequest(query="Rolex")

    assert request.condition == "used"
    assert request.in_stock_only is False
    with pytest.raises(ValueError):
        Channel3SearchRequest(query="Rolex", condition="refurbished")  # type: ignore[arg-type]


def test_filter_keeps_used_offers_and_does_not_mutate_provider_products() -> None:
    original = _product(_offer("used"), _offer("new"), _offer(None))

    filtered, filtered_out_count = filter_channel3_products(
        [original],
        condition="used",
    )

    assert len(filtered) == 1
    assert [offer.condition for offer in filtered[0].offers] == ["used"]
    assert filtered_out_count == 2
    assert [offer.condition for offer in original.offers] == ["used", "new", None]
    assert filtered[0] is not original
    assert filtered[0].offers is not original.offers


def test_filter_keeps_new_offers_and_drops_products_without_them() -> None:
    filtered, filtered_out_count = filter_channel3_products(
        [
            _product(_offer("used"), _offer("new"), _offer(None)),
            _product(_offer("used")),
        ],
        condition="new",
    )

    assert len(filtered) == 1
    assert [offer.condition for offer in filtered[0].offers] == ["new"]
    assert filtered_out_count == 3


def test_filter_all_keeps_everything_and_stock_filter_drops_out_of_stock() -> None:
    product = _product(_offer("new", "OutOfStock"), _offer("used"))
    empty_product = _product()

    all_products, filtered_out_count = filter_channel3_products(
        [product, empty_product],
        condition="all",
    )
    in_stock_products, stock_filtered_count = filter_channel3_products(
        [product],
        condition="all",
        in_stock_only=True,
    )

    assert len(all_products) == 2
    assert [offer.condition for offer in all_products[0].offers] == ["new", "used"]
    assert all_products[1].offers == []
    assert filtered_out_count == 0
    assert [offer.condition for offer in in_stock_products[0].offers] == ["used"]
    assert stock_filtered_count == 1


async def test_channel3_search_stops_after_three_empty_filtered_provider_pages() -> None:
    calls: list[dict[str, object]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.read())
        calls.append(payload)
        provider_result = json.loads(_SEARCH_FIXTURE.read_text(encoding="utf-8"))
        provider_result["next_page_token"] = f"page-{len(calls)}"
        return httpx.Response(200, json=provider_result, request=request)

    client = Channel3Client(
        SecretStr("channel3-test-key"),
        3,
        transport=httpx.MockTransport(handle),
    )

    result = await client.search(
        query="Rolex",
        limit=10,
        page_token=None,
        condition="new",
    )

    assert len(calls) == 3
    assert [call.get("page_token") for call in calls] == [None, "page-1", "page-2"]
    for call in calls:
        filters = call["filters"]
        assert isinstance(filters, dict)
        assert filters["conditions"] == ["new"]
    assert result.products == []
    assert result.filtered_out_count == 3
    assert result.provider_pages_fetched == 3
    assert result.next_page_token == "page-3"


async def test_channel3_search_requires_configured_key() -> None:
    client = Channel3Client(SecretStr(""), 3)

    with pytest.raises(Channel3NotConfiguredError):
        await client.search(query="Rolex", limit=20, page_token=None)


async def test_channel3_search_does_not_include_provider_body_in_errors() -> None:
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
