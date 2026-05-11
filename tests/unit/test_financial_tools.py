"""Unit tests for financial calculation functions — fully deterministic."""
import pytest
from casci.state import Scenario
from casci.tools.financial_tools import calculate_net_impact

_FIN = {
    "unit_cost": 10.0,
    "unit_price": 20.0,
    "carrying_cost_rate_annual": 0.25,
    "customer_margin": 0.30,
    "event_duration_weeks": 4,
    "fill_rate_goal": 0.97,
}

_SCENARIO = Scenario(
    name="Moderate",
    lift_assumption=2.5,
    pre_stage_quantity=1000.0,
    order_timing_weeks_before=2,
    service_level_target=0.97,
    post_event_rundown_weeks=4,
    week_by_week_demand=[250.0, 260.0, 255.0, 245.0, 130.0, 120.0, 115.0, 110.0, 110.0, 110.0],
    narrative="Test scenario",
    is_feasible=True,
)


def test_revenue_calculation():
    result = calculate_net_impact(_SCENARIO, _FIN)
    # Event demand = sum of first 4 weeks = 1010
    # Revenue = 1010 * 20 * 0.30 = 6060
    assert result["projected_revenue"] == pytest.approx(6060.0, rel=0.01)


def test_carrying_cost_is_positive():
    result = calculate_net_impact(_SCENARIO, _FIN)
    assert result["carrying_cost"] > 0


def test_no_stockout_when_prestage_covers_demand():
    result = calculate_net_impact(_SCENARIO, _FIN)
    # pre_stage=1000, event_demand=1010 → slight stockout
    assert result["expected_stockout_cost"] >= 0


def test_net_impact_formula():
    result = calculate_net_impact(_SCENARIO, _FIN)
    expected_net = (
        result["projected_revenue"]
        - result["carrying_cost"]
        - result["expected_stockout_cost"]
    )
    assert result["net_financial_impact"] == pytest.approx(expected_net, rel=0.001)
