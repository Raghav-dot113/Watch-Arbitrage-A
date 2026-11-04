from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from chronoarb.domain.errors import CurrencyMismatchError, ValidationError
from chronoarb.domain.money import Money


@dataclass(frozen=True)
class AcquisitionCosts:
    """Resolved non-negative acquisition cost components in one currency."""

    buyer_fee: Money
    tax_and_duty: Money
    inbound_shipping: Money
    authentication_cost: Money
    service_reserve: Money
    financing_cost: Money
    acquisition_risk_reserve: Money

    @property
    def total(self) -> Money:
        return (
            self.buyer_fee
            + self.tax_and_duty
            + self.inbound_shipping
            + self.authentication_cost
            + self.service_reserve
            + self.financing_cost
            + self.acquisition_risk_reserve
        )


@dataclass(frozen=True)
class ResaleCosts:
    """Resolved non-negative resale cost components in one currency."""

    selling_fee: Money
    outbound_shipping: Money
    resale_payment_cost: Money
    exit_risk_reserve: Money

    @property
    def total(self) -> Money:
        return (
            self.selling_fee
            + self.outbound_shipping
            + self.resale_payment_cost
            + self.exit_risk_reserve
        )


@dataclass(frozen=True)
class CostAssumptions:
    """Versioned, currency-consistent cost amounts resolved for a valuation."""

    version: str
    acquisition: AcquisitionCosts
    resale: ResaleCosts

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValidationError("Cost assumptions version must not be empty")

        acquisition_costs = (
            self.acquisition.buyer_fee,
            self.acquisition.tax_and_duty,
            self.acquisition.inbound_shipping,
            self.acquisition.authentication_cost,
            self.acquisition.service_reserve,
            self.acquisition.financing_cost,
            self.acquisition.acquisition_risk_reserve,
        )
        resale_costs = (
            self.resale.selling_fee,
            self.resale.outbound_shipping,
            self.resale.resale_payment_cost,
            self.resale.exit_risk_reserve,
        )
        _validate_cost_group(acquisition_costs, "acquisition")
        _validate_cost_group(resale_costs, "resale")
        if acquisition_costs[0].currency != resale_costs[0].currency:
            raise CurrencyMismatchError(
                "Acquisition and resale cost assumptions must use the same currency"
            )

    @property
    def currency(self) -> str:
        return self.acquisition.buyer_fee.currency


@dataclass(frozen=True)
class CostBreakdown:
    """Financial totals and source cost components produced by the cost model."""

    cost_assumptions_version: str
    acquisition: AcquisitionCosts
    resale: ResaleCosts
    all_in_acquisition: Money
    expected_net_resale: Money
    expected_net_profit: Money
    roi: Decimal | None


def calculate_cost_breakdown(
    purchase_price: Money,
    expected_exit_price: Money,
    assumptions: CostAssumptions,
) -> CostBreakdown:
    """Calculate totals from resolved cost inputs; ROI is undefined for zero acquisition."""
    _validate_price(purchase_price, "Purchase price")
    _validate_price(expected_exit_price, "Expected exit price")
    if purchase_price.currency != assumptions.currency:
        raise CurrencyMismatchError("Purchase price currency must match cost assumptions currency")
    if expected_exit_price.currency != assumptions.currency:
        raise CurrencyMismatchError(
            "Expected exit price currency must match cost assumptions currency"
        )

    all_in_acquisition = purchase_price + assumptions.acquisition.total
    expected_net_resale = expected_exit_price - assumptions.resale.total
    expected_net_profit = expected_net_resale - all_in_acquisition
    roi = (
        expected_net_profit.amount / all_in_acquisition.amount
        if all_in_acquisition.amount != 0
        else None
    )
    return CostBreakdown(
        cost_assumptions_version=assumptions.version,
        acquisition=assumptions.acquisition,
        resale=assumptions.resale,
        all_in_acquisition=all_in_acquisition,
        expected_net_resale=expected_net_resale,
        expected_net_profit=expected_net_profit,
        roi=roi,
    )


def _validate_cost_group(costs: tuple[Money, ...], group: str) -> None:
    currency = costs[0].currency
    for cost in costs:
        if cost.currency != currency:
            raise CurrencyMismatchError(f"All {group} costs must use the same currency")
        if not cost.amount.is_finite() or cost.amount < 0:
            raise ValidationError(f"{group.capitalize()} costs must be finite and non-negative")


def _validate_price(price: Money, name: str) -> None:
    if not price.amount.is_finite() or price.amount < 0:
        raise ValidationError(f"{name} must be finite and non-negative")
