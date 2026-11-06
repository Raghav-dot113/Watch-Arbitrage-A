from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from chronoarb.domain.errors import ValidationError

CENT = Decimal("0.01")


@dataclass(frozen=True)
class ValuationInput:
    expected_exit_price: Decimal
    exit_price_currency: str
    normalized_price: Decimal
    normalized_currency: str
    fees: Decimal = Decimal("0")
    duties: Decimal = Decimal("0")
    shipping: Decimal = Decimal("0")
    risk_reserve: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if self.exit_price_currency != self.normalized_currency:
            raise ValidationError("Valuation currencies must match at this stage")
        values = (
            self.expected_exit_price,
            self.normalized_price,
            self.fees,
            self.duties,
            self.shipping,
            self.risk_reserve,
        )
        if any(not isinstance(value, Decimal) or value < 0 for value in values):
            raise ValidationError("Valuation amounts must be non-negative Decimal values")


@dataclass(frozen=True)
class ValuationResult:
    expected_exit_price: Decimal
    all_in_acquisition: Decimal
    expected_net_resale: Decimal
    expected_net_profit: Decimal
    roi: Decimal
    currency: str
    cost_breakdown: dict[str, str]


def money(value: Decimal) -> Decimal:
    try:
        return value.quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValidationError("Invalid monetary value") from None


def calculate_valuation(value: ValuationInput) -> ValuationResult:
    all_in = money(
        value.normalized_price + value.fees + value.duties + value.shipping + value.risk_reserve
    )
    net_resale = money(value.expected_exit_price - value.risk_reserve)
    profit = money(net_resale - all_in)
    roi = money(profit / all_in) if all_in else Decimal("0")
    return ValuationResult(
        expected_exit_price=money(value.expected_exit_price),
        all_in_acquisition=all_in,
        expected_net_resale=net_resale,
        expected_net_profit=profit,
        roi=roi,
        currency=value.exit_price_currency,
        cost_breakdown={
            "fees": str(money(value.fees)),
            "duties": str(money(value.duties)),
            "shipping": str(money(value.shipping)),
            "risk_reserve": str(money(value.risk_reserve)),
        },
    )
