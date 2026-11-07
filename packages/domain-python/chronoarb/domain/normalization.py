from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from chronoarb.domain.errors import ValidationError


@dataclass(frozen=True)
class NormalizedListingInput:
    listing_price: Decimal
    price_currency: str
    fx_rate: Decimal
    fx_source: str
    reference_id: str
    match_confidence: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.listing_price, Decimal) or self.listing_price < 0:
            raise ValidationError("listing_price must be a non-negative Decimal")
        if not isinstance(self.fx_rate, Decimal) or self.fx_rate <= 0:
            raise ValidationError("fx_rate must be a positive Decimal")
        if not self.price_currency or len(self.price_currency) != 3:
            raise ValidationError("price_currency must be a three-character code")
        if not 0 <= self.match_confidence <= 1:
            raise ValidationError("match_confidence must be between zero and one")


@dataclass(frozen=True)
class NormalizedListingResult:
    normalized_price: Decimal
    normalized_currency: str
    reference_id: str
    match_confidence: Decimal
    fx_rate: Decimal
    fx_source: str


def normalize_listing(
    value: NormalizedListingInput, target_currency: str = "USD"
) -> NormalizedListingResult:
    normalized_price = (value.listing_price * value.fx_rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return NormalizedListingResult(
        normalized_price=normalized_price,
        normalized_currency=target_currency,
        reference_id=value.reference_id,
        match_confidence=value.match_confidence,
        fx_rate=value.fx_rate,
        fx_source=value.fx_source,
    )
