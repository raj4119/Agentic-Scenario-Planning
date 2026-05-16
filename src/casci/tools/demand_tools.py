"""
Demand-side tool functions for the Demand Decomposition Agent.

Each function wraps one of the SQL queries from the Baseline Events workbook:
  get_event_details()       → Query 1: Customer + Event Identification
  get_baseline_demand()     → Query 2: Pre-event baseline weekly avg (sales signal, 8-week trailing)
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
# Query 2 — Pre-event baseline weekly average (8-week trailing, sales signal only)
# Planned uplift is dropped — scenarios are driven by comparable event actuals (Query 4).
# ---------------------------------------------------------------------------
_QUERY_BASELINE_DEMAND = """
WITH event_plc AS (
    SELECT plc.id AS plc_id
    FROM event_prod_loc_cust_xref eplcx
    JOIN product_location_customer_xref plc ON plc.id = eplcx.prod_loc_cust_id
    WHERE eplcx.event_id = :event_id
      AND eplcx.is_deleted = 0
),
baseline_periods AS (
    SELECT dp.period_number
    FROM event e
    JOIN period dp
      ON dp.period_end   <  e.start_date
     AND dp.period_end   >= DATEADD(week, -8, e.start_date)
    WHERE e.id = :event_id
),
weekly_totals AS (
    SELECT
        unpvt.period_number,
        SUM(unpvt.demand_value) AS weekly_total
    FROM demand_history dh
    JOIN demand_signal ds
      ON ds.id = dh.demand_signal_id AND ds.name = 'sales'
    JOIN event_plc ep ON ep.plc_id = dh.prod_loc_cust_id
    CROSS APPLY (VALUES
        ( 1,dh.P1),  ( 2,dh.P2),  ( 3,dh.P3),  ( 4,dh.P4),
        ( 5,dh.P5),  ( 6,dh.P6),  ( 7,dh.P7),  ( 8,dh.P8),
        ( 9,dh.P9),  (10,dh.P10), (11,dh.P11), (12,dh.P12),
        (13,dh.P13), (14,dh.P14), (15,dh.P15), (16,dh.P16),
        (17,dh.P17), (18,dh.P18), (19,dh.P19), (20,dh.P20),
        (21,dh.P21), (22,dh.P22), (23,dh.P23), (24,dh.P24),
        (25,dh.P25), (26,dh.P26), (27,dh.P27), (28,dh.P28),
        (29,dh.P29), (30,dh.P30), (31,dh.P31), (32,dh.P32),
        (33,dh.P33), (34,dh.P34), (35,dh.P35), (36,dh.P36),
        (37,dh.P37), (38,dh.P38), (39,dh.P39), (40,dh.P40),
        (41,dh.P41), (42,dh.P42), (43,dh.P43), (44,dh.P44),
        (45,dh.P45), (46,dh.P46), (47,dh.P47), (48,dh.P48),
        (49,dh.P49), (50,dh.P50), (51,dh.P51), (52,dh.P52),
        (53,dh.P53), (54,dh.P54), (55,dh.P55), (56,dh.P56),
        (57,dh.P57), (58,dh.P58), (59,dh.P59), (60,dh.P60),
        (61,dh.P61), (62,dh.P62), (63,dh.P63), (64,dh.P64),
        (65,dh.P65), (66,dh.P66), (67,dh.P67), (68,dh.P68),
        (69,dh.P69), (70,dh.P70), (71,dh.P71), (72,dh.P72),
        (73,dh.P73), (74,dh.P74), (75,dh.P75), (76,dh.P76),
        (77,dh.P77), (78,dh.P78), (79,dh.P79), (80,dh.P80),
        (81,dh.P81), (82,dh.P82), (83,dh.P83), (84,dh.P84),
        (85,dh.P85), (86,dh.P86), (87,dh.P87), (88,dh.P88),
        (89,dh.P89), (90,dh.P90), (91,dh.P91), (92,dh.P92),
        (93,dh.P93), (94,dh.P94), (95,dh.P95), (96,dh.P96),
        (97,dh.P97), (98,dh.P98), (99,dh.P99),(100,dh.P100),
       (101,dh.P101),(102,dh.P102),(103,dh.P103),(104,dh.P104),
       (105,dh.P105),(106,dh.P106),(107,dh.P107),(108,dh.P108),
       (109,dh.P109),(110,dh.P110),(111,dh.P111),(112,dh.P112),
       (113,dh.P113),(114,dh.P114),(115,dh.P115),(116,dh.P116),
       (117,dh.P117),(118,dh.P118),(119,dh.P119),(120,dh.P120),
       (121,dh.P121),(122,dh.P122),(123,dh.P123),(124,dh.P124),
       (125,dh.P125),(126,dh.P126),(127,dh.P127),(128,dh.P128),
       (129,dh.P129),(130,dh.P130),(131,dh.P131),(132,dh.P132),
       (133,dh.P133),(134,dh.P134),(135,dh.P135),(136,dh.P136),
       (137,dh.P137),(138,dh.P138),(139,dh.P139),(140,dh.P140),
       (141,dh.P141),(142,dh.P142),(143,dh.P143),(144,dh.P144),
       (145,dh.P145),(146,dh.P146),(147,dh.P147),(148,dh.P148),
       (149,dh.P149),(150,dh.P150),(151,dh.P151),(152,dh.P152),
       (153,dh.P153),(154,dh.P154),(155,dh.P155),(156,dh.P156)
    ) AS unpvt(period_number, demand_value)
    JOIN baseline_periods bp ON bp.period_number = unpvt.period_number
    WHERE unpvt.demand_value IS NOT NULL
    GROUP BY unpvt.period_number
)
SELECT AVG(weekly_total) AS baseline_weekly_avg
FROM weekly_totals
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
    """Query 2 — Pre-event baseline weekly average.

    Averages weekly sales demand across the 8 weeks before the event start,
    summing across all product-location-customer combinations for the event.
    Uses demand_signal='sales' only — planned uplift is not used here.

    Returns:
        baseline_weekly_avg: float — average weekly demand in the 8-week pre-event window
    """
    rows = execute_query(_QUERY_BASELINE_DEMAND, {"event_id": event_id})
    if not rows or rows[0]["baseline_weekly_avg"] is None:
        raise ValueError(f"No baseline demand found for event_id={event_id}")
    return {"baseline_weekly_avg": float(rows[0]["baseline_weekly_avg"])}


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
