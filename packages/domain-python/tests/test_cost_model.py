from dataclasses import replace
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from chronoarb.domain.cost_model import (
    AcquisitionCosts,
    CostAssumptions,
    ResaleCosts,
    calculate_cost_breakdown,
)
from chronoarb.domain.errors import CurrencyMismatchError, ValidationError
from chronoarb.domain.money import Money

_money_amounts = st.integers(min_value=0, max_value=100_000_000)


def _money(minor_units: int, currency: str = "USD") -> Money:
    return Money(Decimal(minor_units).scaleb(-2), currency)


_money_values = _money_amounts.map(_money)
_acquisition_costs = st.builds(
    AcquisitionCosts,
    buyer_fee=_money_values,
    tax_and_duty=_money_values,
    inbound_shipping=_money_values,
    authentication_cost=_money_values,
    service_reserve=_money_values,
    financing_cost=_money_values,
    acquisition_risk_reserve=_money_values,
)
_resale_costs = st.builds(
    ResaleCosts,
    selling_fee=_money_values,
    outbound_shipping=_money_values,
    resale_payment_cost=_money_values,
    exit_risk_reserve=_money_values,
)
_assumptions = st.builds(
    CostAssumptions,
    version=st.just("test-v1"),
    acquisition=_acquisition_costs,
    resale=_resale_costs,
)


@given(
    purchase_price=_money_values,
    expected_exit_price=_money_values,
    assumptions=_assumptions,
)
def test_cost_breakdown_preserves_financial_identities(
    purchase_price: Money,
    expected_exit_price: Money,
    assumptions: CostAssumptions,
) -> None:
    result = calculate_cost_breakdown(purchase_price, expected_exit_price, assumptions)

    assert result.cost_assumptions_version == assumptions.version
    assert result.all_in_acquisition == purchase_price + assumptions.acquisition.total
    assert result.expected_net_resale == expected_exit_price - assumptions.resale.total
    assert result.expected_net_profit == result.expected_net_resale - result.all_in_acquisition
    if result.all_in_acquisition.amount == 0:
        assert result.roi is None
    else:
        assert result.roi == (result.expected_net_profit.amount / result.all_in_acquisition.amount)


@given(
    purchase_price=_money_values,
    expected_exit_price=_money_values,
    assumptions=_assumptions,
    additional_cost=_money_values,
)
def test_additional_acquisition_cost_reduces_profit_by_same_amount(
    purchase_price: Money,
    expected_exit_price: Money,
    assumptions: CostAssumptions,
    additional_cost: Money,
) -> None:
    updated_acquisition = replace(
        assumptions.acquisition,
        buyer_fee=assumptions.acquisition.buyer_fee + additional_cost,
    )
    updated_assumptions = replace(assumptions, acquisition=updated_acquisition)

    before = calculate_cost_breakdown(purchase_price, expected_exit_price, assumptions)
    after = calculate_cost_breakdown(purchase_price, expected_exit_price, updated_assumptions)

    assert after.expected_net_profit == before.expected_net_profit - additional_cost


def test_cost_breakdown_uses_expected_financial_components() -> None:
    assumptions = CostAssumptions(
        version="dealer-costs-v3",
        acquisition=AcquisitionCosts(
            buyer_fee=_money(100_000),
            tax_and_duty=_money(20_000),
            inbound_shipping=_money(10_000),
            authentication_cost=_money(15_000),
            service_reserve=_money(30_000),
            financing_cost=_money(5_000),
            acquisition_risk_reserve=_money(20_000),
        ),
        resale=ResaleCosts(
            selling_fee=_money(60_000),
            outbound_shipping=_money(10_000),
            resale_payment_cost=_money(5_000),
            exit_risk_reserve=_money(10_000),
        ),
    )

    result = calculate_cost_breakdown(_money(1_000_000), _money(1_585_000), assumptions)

    assert result.all_in_acquisition == _money(1_200_000)
    assert result.expected_net_resale == _money(1_500_000)
    assert result.expected_net_profit == _money(300_000)
    assert result.roi == Decimal("0.25")


def test_zero_acquisition_basis_has_no_roi() -> None:
    assumptions = CostAssumptions(
        version="zero-v1",
        acquisition=AcquisitionCosts(*(_money(0) for _ in range(7))),
        resale=ResaleCosts(*(_money(0) for _ in range(4))),
    )

    result = calculate_cost_breakdown(_money(0), _money(100), assumptions)

    assert result.all_in_acquisition == _money(0)
    assert result.roi is None


def test_cost_assumptions_reject_negative_costs() -> None:
    acquisition = AcquisitionCosts(
        buyer_fee=_money(-1),
        tax_and_duty=_money(0),
        inbound_shipping=_money(0),
        authentication_cost=_money(0),
        service_reserve=_money(0),
        financing_cost=_money(0),
        acquisition_risk_reserve=_money(0),
    )

    with pytest.raises(ValidationError, match="non-negative"):
        CostAssumptions(
            version="dealer-v1",
            acquisition=acquisition,
            resale=ResaleCosts(*(_money(0) for _ in range(4))),
        )


def test_cost_assumptions_reject_mixed_currencies() -> None:
    acquisition = AcquisitionCosts(
        buyer_fee=_money(0),
        tax_and_duty=_money(0),
        inbound_shipping=_money(0),
        authentication_cost=_money(0),
        service_reserve=_money(0),
        financing_cost=_money(0),
        acquisition_risk_reserve=_money(0),
    )
    resale = ResaleCosts(
        selling_fee=_money(0),
        outbound_shipping=_money(0, "EUR"),
        resale_payment_cost=_money(0),
        exit_risk_reserve=_money(0),
    )

    with pytest.raises(CurrencyMismatchError):
        CostAssumptions(version="dealer-v1", acquisition=acquisition, resale=resale)


@pytest.mark.parametrize("price", [Money(Decimal("-0.01"), "USD"), Money(Decimal("NaN"), "USD")])
def test_calculation_rejects_negative_or_non_finite_prices(price: Money) -> None:
    assumptions = CostAssumptions(
        version="dealer-v1",
        acquisition=AcquisitionCosts(*(_money(0) for _ in range(7))),
        resale=ResaleCosts(*(_money(0) for _ in range(4))),
    )

    with pytest.raises(ValidationError):
        calculate_cost_breakdown(price, _money(100), assumptions)


def test_cost_assumptions_reject_empty_version() -> None:
    with pytest.raises(ValidationError, match="version"):
        CostAssumptions(
            version=" ",
            acquisition=AcquisitionCosts(*(_money(0) for _ in range(7))),
            resale=ResaleCosts(*(_money(0) for _ in range(4))),
        )
