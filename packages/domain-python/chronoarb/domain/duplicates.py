from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DuplicateCandidate:
    listing_id: str
    reference_id: str
    normalized_price: Decimal
    seller_geography: str | None
    external_url: str | None


def duplicate_confidence(first: DuplicateCandidate, second: DuplicateCandidate) -> Decimal:
    if first.reference_id != second.reference_id:
        return Decimal("0")
    score = Decimal("0.4")
    if first.external_url and first.external_url == second.external_url:
        score += Decimal("0.4")
    if first.seller_geography and first.seller_geography == second.seller_geography:
        score += Decimal("0.1")
    if first.normalized_price == second.normalized_price:
        score += Decimal("0.1")
    return min(score, Decimal("1"))
