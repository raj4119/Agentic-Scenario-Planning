"""
Supply-side tool functions for the Supply Constraint Agent.

  get_oos_history()         → Query 3: OOS + Overstock + Service Levels (±8 week window)
  get_inventory_position()  → Query 5: Supply Constraint Snapshot at T-14
"""

from casci.tools.db import execute_query

_QUERY_OOS_HISTORY = """
-- TODO: paste Query 3 SQL from Baseline Events workbook
-- Returns: OOS/overstock flags, ATP, safety stock, fill rate, lead times
--          across ±8 weeks of the event window
SELECT 1 AS placeholder WHERE 1=0
"""

_QUERY_INVENTORY_POSITION = """
-- TODO: paste Query 5 SQL from Baseline Events workbook
-- Returns: ATP at T-14, lead-time feasibility, MOQ, max order qty,
--          sourcing network policy notes
SELECT 1 AS placeholder WHERE 1=0
"""


def get_oos_history(event_id: int) -> list[dict]:
    """Query 3 — OOS + Overstock + Service Levels.

    Scans product_location_xref_history across ±8 weeks of the event window.
    Flags out-of-stock and overstock conditions, computes ATP, and tracks
    safety stock, fill rate goals, and lead times at each snapshot interval.
    """
    return execute_query(_QUERY_OOS_HISTORY, {"event_id": event_id})


def get_inventory_position(event_id: int) -> dict:
    """Query 5 — Supply Constraint Snapshot at T-14.

    Reconstructs inventory and sourcing state exactly 14 days before event
    start using history tables.

    Returns:
        available_to_promise: float
        lead_time_days: int
        is_prestage_feasible: bool  — True if lead time allows pre-stage order
        min_order_qty: float
        max_order_qty: float
        sourcing_notes: str
    """
    rows = execute_query(_QUERY_INVENTORY_POSITION, {"event_id": event_id})
    if not rows:
        raise ValueError(f"No inventory snapshot found for event_id={event_id}")

    row = rows[0]
    return {
        "available_to_promise": float(row["atp"]),
        "lead_time_days": int(row["lead_time_days"]),
        "is_prestage_feasible": bool(row["lead_time_feasible"]),
        "min_order_qty": float(row["moq"]),
        "max_order_qty": float(row["max_order_qty"]),
        "sourcing_notes": row.get("sourcing_notes", ""),
    }
