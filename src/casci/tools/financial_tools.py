"""
Financial tool functions for the Financial Impact Agent.

  get_financial_inputs() → Query 6: Cost, price, carrying rate, margin, event duration
  calculate_net_impact() → Pure Python — deterministic financial formulas (no LLM)
"""

from casci.tools.db import execute_query
from casci.state import Scenario

_QUERY_FINANCIAL_INPUTS = """
-- TODO: paste Query 6 SQL from Baseline Events workbook
-- Returns: unit_cost, unit_price, carrying_cost_rate, customer_margin,
--          event_duration_weeks, fill_rate_goal
SELECT 1 AS placeholder WHERE 1=0
"""


def get_financial_inputs(event_id: int) -> dict:
    """Query 6 — Financial Inputs as of T-14.

    Returns:
        unit_cost: float
        unit_price: float
        carrying_cost_rate_annual: float  — e.g. 0.25 for 25% per year
        customer_margin: float            — e.g. 0.30 for 30% gross margin
        event_duration_weeks: int
        fill_rate_goal: float
    """
    rows = execute_query(_QUERY_FINANCIAL_INPUTS, {"event_id": event_id})
    if not rows:
        raise ValueError(f"No financial inputs found for event_id={event_id}")

    row = rows[0]
    return {
        "unit_cost": float(row["unit_cost"]),
        "unit_price": float(row["unit_price"]),
        "carrying_cost_rate_annual": float(row["carrying_cost_rate"]),
        "customer_margin": float(row["customer_margin"]),
        "event_duration_weeks": int(row["event_duration_weeks"]),
        "fill_rate_goal": float(row["fill_rate_goal"]),
    }


def calculate_net_impact(scenario: Scenario, fin: dict) -> dict:
    """Deterministic financial calculation for one scenario.

    All numbers are computed here — the LLM never generates financial figures.

    Args:
        scenario: the Scenario dataclass from the Scenario Generator Agent
        fin: output of get_financial_inputs()

    Returns dict with keys:
        projected_revenue, carrying_cost, expected_stockout_cost, net_financial_impact
    """
    duration_weeks = fin["event_duration_weeks"]
    event_demand = sum(scenario.week_by_week_demand[:duration_weeks])

    projected_revenue = event_demand * fin["unit_price"] * fin["customer_margin"]

    carrying_cost = (
        scenario.pre_stage_quantity
        * fin["unit_cost"]
        * (fin["carrying_cost_rate_annual"] / 52)
        * scenario.post_event_rundown_weeks
    )

    shortage_units = max(0.0, event_demand - scenario.pre_stage_quantity)
    expected_stockout_cost = shortage_units * fin["unit_price"] * fin["customer_margin"]

    net_financial_impact = projected_revenue - carrying_cost - expected_stockout_cost

    return {
        "projected_revenue": round(projected_revenue, 2),
        "carrying_cost": round(carrying_cost, 2),
        "expected_stockout_cost": round(expected_stockout_cost, 2),
        "net_financial_impact": round(net_financial_impact, 2),
    }
