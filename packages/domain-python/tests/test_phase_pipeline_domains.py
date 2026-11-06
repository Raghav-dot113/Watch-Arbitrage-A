from decimal import Decimal

from chronoarb.domain.duplicates import DuplicateCandidate, duplicate_confidence
from chronoarb.domain.normalization import NormalizedListingInput, normalize_listing
from chronoarb.domain.valuation import ValuationInput, calculate_valuation


def test_normalization_uses_decimal() -> None:
    result = normalize_listing(
        NormalizedListingInput(
            listing_price=Decimal("100.00"),
            price_currency="EUR",
            fx_rate=Decimal("1.10"),
            fx_source="fixture",
            reference_id="ref_1",
            match_confidence=Decimal("0.95"),
        )
    )
    assert result.normalized_price == Decimal("110.00")
    assert result.normalized_currency == "USD"


def test_valuation_profit_and_roi_are_decimal() -> None:
    result = calculate_valuation(
        ValuationInput(
            expected_exit_price=Decimal("500.00"),
            exit_price_currency="USD",
            normalized_price=Decimal("400.00"),
            normalized_currency="USD",
            fees=Decimal("10.00"),
            shipping=Decimal("20.00"),
        )
    )
    assert result.all_in_acquisition == Decimal("430.00")
    assert result.expected_net_profit == Decimal("70.00")
    assert result.roi == Decimal("0.16")


def test_duplicate_confidence_is_deterministic() -> None:
    first = DuplicateCandidate("lst_1", "ref_1", Decimal("100"), "US", "https://example.test/watch")
    second = DuplicateCandidate(
        "lst_2", "ref_1", Decimal("100"), "US", "https://example.test/watch"
    )
    assert duplicate_confidence(first, second) == Decimal("1")


def test_duplicate_confidence_rejects_different_references() -> None:
    first = DuplicateCandidate("lst_1", "ref_1", Decimal("100"), None, None)
    second = DuplicateCandidate("lst_2", "ref_2", Decimal("100"), None, None)
    assert duplicate_confidence(first, second) == Decimal("0")
