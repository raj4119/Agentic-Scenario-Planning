"""
Demand-side tool functions for the Demand Decomposition Agent.

Each function wraps one of the SQL queries from the Baseline Events workbook:
  get_event_details()       → Query 1: Customer + Event Identification
  get_baseline_demand()     → Query 2: Planned vs Actual Uplift
  find_similar_events()     → Query 4: Comparable Event Matching + p25/p50/p75 lift ratios
  get_product_substitutes() → Query 7: Cannibalization Candidates
"""

from casci.tools.db import execute_query

# ---------------------------------------------------------------------------
# Paste the SQL from Query 1 here (parameterised on :event_id)
# ---------------------------------------------------------------------------
_QUERY_EVENT_DETAILS = """
-- TODO: paste Query 1 SQL from Baseline Events workbook
-- Returns: one row per product-location-customer for the event
SELECT 1 AS placeholder WHERE 1=0
"""

# ---------------------------------------------------------------------------
# Paste the SQL from Query 2 here (parameterised on :event_id)
# ---------------------------------------------------------------------------
_QUERY_BASELINE_DEMAND = """
-- TODO: paste Query 2 SQL from Baseline Events workbook
-- Returns: planned uplift history (T-14 snapshot) + actual demand_history periods
SELECT 1 AS placeholder WHERE 1=0
"""

# ---------------------------------------------------------------------------
# Paste the SQL from Query 4 here (parameterised on :event_id)
# ---------------------------------------------------------------------------
_QUERY_COMPARABLE_EVENTS = """
-- TODO: paste Query 4 SQL from Baseline Events workbook
-- Returns: comparable events + lift_p25 / lift_p50 / lift_p75 + confidence_tier
SELECT 1 AS placeholder WHERE 1=0
"""

# ---------------------------------------------------------------------------
# Paste the SQL from Query 7 here (parameterised on :event_id)
# ---------------------------------------------------------------------------
_QUERY_SUBSTITUTES = """
-- TODO: paste Query 7 SQL from Baseline Events workbook
-- Returns: substitute SKUs + pre-event baseline + cannibalization_factor
SELECT 1 AS placeholder WHERE 1=0
"""


def get_event_details(event_id: int) -> list[dict]:
    """Query 1 — Customer + Event Identification.

    Returns one row per product-location-customer combination for the event,
    including product class/group/family, customer segment, planned uplift,
    demand, order quantity, and recalc flag.
    """
    rows = execute_query(_QUERY_EVENT_DETAILS, {"event_id": event_id})
    if not rows:
        raise ValueError(f"No event found for event_id={event_id}")
    return rows


def get_baseline_demand(event_id: int) -> dict:
    """Query 2 — Planned vs Actual Uplift.

    Snapshots uplift history as of T-14 (planned branch) and unpivots
    demand_history periods P1-P156 for the event window (actual branch).

    Returns:
        baseline_weekly_avg: float — average weekly demand excluding promo periods
        planned_uplift_history: list[dict]
        actual_demand_during: list[dict]
    """
    rows = execute_query(_QUERY_BASELINE_DEMAND, {"event_id": event_id})

    planned = [r for r in rows if r.get("branch") == "planned"]
    actual  = [r for r in rows if r.get("branch") == "actual"]

    baseline_values = [r["demand"] for r in actual if r.get("is_baseline_period")]
    baseline_avg = sum(baseline_values) / len(baseline_values) if baseline_values else 0.0

    return {
        "baseline_weekly_avg": baseline_avg,
        "planned_uplift_history": planned,
        "actual_demand_during": actual,
    }


def find_similar_events(event_id: int) -> dict:
    """Query 4 — Comparable Event Matching + Lift Ratios.

    Three-CTE pipeline: anchor → comparable_events → comp_lift.
    Pre-computes p25/p50/p75 lift ratios and assigns a confidence tier
    based on the number of comparable events found.

    Returns:
        comparables: list[dict] — matched historical events with actuals
        lift_p25: float — conservative scenario lift (p25)
        lift_p50: float — moderate scenario lift (p50)
        lift_p75: float — aggressive scenario lift (p75)
        confidence_tier: str — "HIGH" | "MEDIUM" | "LOW"
        comparable_count: int
    """
    rows = execute_query(_QUERY_COMPARABLE_EVENTS, {"event_id": event_id})

    if not rows:
        return {
            "comparables": [],
            "lift_p25": 1.5,
            "lift_p50": 2.0,
            "lift_p75": 2.5,
            "confidence_tier": "LOW",
            "comparable_count": 0,
        }

    # Query 4 returns aggregate row(s) with percentile columns
    agg = rows[0]
    return {
        "comparables": rows,
        "lift_p25": float(agg["lift_p25"]),
        "lift_p50": float(agg["lift_p50"]),
        "lift_p75": float(agg["lift_p75"]),
        "confidence_tier": agg["confidence_tier"],
        "comparable_count": int(agg.get("comparable_count", len(rows))),
    }


def get_product_substitutes(event_id: int) -> list[dict]:
    """Query 7 — Cannibalization Candidates.

    Identifies substitute SKUs in the same product class at the same location.
    Returns cannibalization_factor: either -0.20 (default) or actual
    ratio of during/baseline - 1.0 if historical data exists.
    """
    return execute_query(_QUERY_SUBSTITUTES, {"event_id": event_id})
