"""
Financial tool functions for the Financial Impact Agent.

  get_financial_inputs() → Query 6: Cost, price, carrying rate, margin, event duration
  calculate_net_impact() → Pure Python — deterministic financial formulas (no LLM)
"""

from casci.tools.db import execute_query
from casci.state import Scenario

_QUERY_FINANCIAL_INPUTS = """
SELECT
    p.id   AS product_id,
    p.code AS product_code,
    l.id   AS location_id,
    l.code AS location_code,
    c.id   AS customer_id,
    c.code AS customer_code,
    pl_h.current_cost                                       AS unit_cost,
    pl_h.current_price                                      AS unit_price,
    pl_h.line_cost,
    pl_h.carrying_cost                                      AS carrying_cost_rate,
    pl_h.fill_rate_goal,
    pl_h.service_level_objective,
    DATEDIFF(week, e.start_date, e.end_date) + 1           AS event_duration_weeks,
    cs.min_margin,
    cs.max_margin,
    (cs.min_margin + cs.max_margin) / 2.0                  AS customer_margin
FROM event e
JOIN event_prod_loc_cust_xref eplcx
    ON eplcx.event_id = e.id AND eplcx.is_deleted = 0
JOIN product_location_customer_xref plc
    ON plc.id = eplcx.prod_loc_cust_id
JOIN product p   ON p.id  = plc.product_id
JOIN location l  ON l.id  = plc.location_id
JOIN customer c  ON c.id  = plc.customer_id
JOIN customer_segment cs ON cs.id = c.segment_id
JOIN dbo.product_location_xref_history pl_h
    ON  pl_h.product_id  = plc.product_id
    AND pl_h.location_id = plc.location_id
    AND pl_h.StartTime  <= (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id)
    AND pl_h.EndTime     > (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id)
WHERE e.id = :event_id AND e.is_deleted = 0
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
