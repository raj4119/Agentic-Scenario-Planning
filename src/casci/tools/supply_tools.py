"""
Supply-side tool functions for the Supply Constraint Agent.

  get_oos_history()         → Query 3: OOS + Overstock + Service Levels (±8 week window)
  get_inventory_position()  → Query 5: Supply Constraint Snapshot at T-14
"""

from casci.tools.db import execute_query

_QUERY_OOS_HISTORY = """
SELECT
    plc.product_id,
    plc.location_id,
    h.StartTime                     AS snapshot_from,
    h.EndTime                       AS snapshot_to,
    CASE
        WHEN h.StartTime < e.start_date THEN 'pre'
        WHEN h.StartTime > e.end_date   THEN 'post'
        ELSE 'during'
    END                             AS promo_window,
    h.inventory_BOH,
    h.inventory_onorder,
    h.inventory_backorder,
    h.inventory_reserved,
    h.total_on_hold_quantity,
    h.inventory_BOH
        - ISNULL(h.inventory_reserved, 0)
        + ISNULL(h.inventory_onorder, 0)  AS available_to_promise,
    h.safety_stock_units,
    h.system_safety_stock_units,
    h.buy_safety_stock_units,
    h.safety_stock_in_effect,
    h.out_of_stock_point,
    h.out_of_stock_days,
    CASE
        WHEN h.inventory_BOH <= h.out_of_stock_point THEN 1
        ELSE 0
    END                             AS is_oos_flag,
    h.overstock_units,
    h.overstock_amount,
    CASE
        WHEN h.overstock_units > 0 THEN 1
        ELSE 0
    END                             AS is_overstock_flag,
    h.fill_rate_goal,
    h.fill_rate_goal_el,
    h.service_level_objective,
    h.lead_time_days
FROM dbo.product_location_xref_history h
JOIN event_prod_loc_cust_xref eplcx ON eplcx.event_id = :event_id
JOIN product_location_customer_xref plc ON plc.id     = eplcx.prod_loc_cust_id
JOIN event e ON e.id                                  = :event_id
  AND h.location_id = plc.location_id
  AND h.EndTime     >= DATEADD(week, -8, e.start_date)
  AND h.StartTime   <= DATEADD(week,  6, e.end_date)
ORDER BY h.StartTime
"""

_QUERY_INVENTORY_POSITION = """
SELECT
    plc.product_id,
    plc.location_id,
    pl_h.inventory_BOH,
    pl_h.inventory_onorder,
    pl_h.inventory_reserved,
    pl_h.inventory_backorder,
    pl_h.total_on_hold_quantity,
    pl_h.inventory_BOH
        - ISNULL(pl_h.inventory_reserved, 0)
        + ISNULL(pl_h.inventory_onorder,  0)                AS atp,
    ISNULL(sn_h.quoted_lead_time, pl_h.lead_time_days)      AS lead_time_days,
    pl_h.lead_time_days                                     AS pl_lead_time_days,
    sn_h.quoted_lead_time                                   AS sn_quoted_lead_time,
    sn_h.source_transit_time,
    sn_h.total_lead_time,
    psn_h.min_purchase_quantity                             AS moq,
    psn_h.minimum_order_units,
    psn_h.maximum_order_units                               AS max_order_qty,
    psn_h.hard_maximum_units,
    psn_h.buying_multiple_units,
    DATEDIFF(day,
        (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id),
        e.start_date)                                       AS days_until_event,
    CASE
        WHEN DATEDIFF(day,
                (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id),
                e.start_date)
             >= ISNULL(sn_h.quoted_lead_time, pl_h.lead_time_days)
        THEN 1 ELSE 0
    END                                                     AS lead_time_feasible,
    CASE
        WHEN DATEDIFF(day,
                (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id),
                e.start_date)
             < ISNULL(sn_h.quoted_lead_time, pl_h.lead_time_days)
        THEN 'ATP only — lead time exceeds remaining window'
        ELSE 'Pre-stage order feasible'
    END                                                     AS sourcing_notes,
    sn.id                                                   AS sourcing_network_id,
    sn.order_policy
FROM event e
JOIN event_prod_loc_cust_xref eplcx ON eplcx.event_id  = e.id
                                    AND eplcx.is_deleted = 0
JOIN product_location_customer_xref plc ON plc.id      = eplcx.prod_loc_cust_id
JOIN dbo.product_location_xref_history pl_h
    ON  pl_h.product_id  = plc.product_id
    AND pl_h.location_id = plc.location_id
    AND pl_h.StartTime  <= (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id)
    AND pl_h.EndTime     > (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id)
LEFT JOIN product_sourcing_network_xref_History psn_h
    ON  psn_h.product_id = plc.product_id
    AND psn_h.StartTime <= (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id)
    AND psn_h.EndTime    > (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id)
LEFT JOIN sourcing_network sn
    ON  sn.id = psn_h.sourcingnetwork_id
    AND sn.to_location = plc.location_id
LEFT JOIN dbo.sourcing_network_History sn_h
    ON  sn_h.id         = sn.id
    AND sn_h.StartTime <= (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id)
    AND sn_h.EndTime    > (SELECT CAST(DATEADD(day, -14, start_date) AS DATE) FROM event WHERE id = :event_id)
WHERE e.id = :event_id
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
