-- ============================================================
-- CASCI Scenario Planning — Parameterized SQL Queries
-- All queries use :event_id as the SQLAlchemy bind parameter.
-- Column aliases match the Python tool function return dicts.
--
-- Source: Baseline Events (originally hardcoded event 41)
-- Changes from source:
--   - All = 41 / <> 41 replaced with = :event_id / <> :event_id
--   - Column aliases corrected to match Python tool return keys
--   - Q2 redesigned 2026-05-15: planned uplift dropped, 8-week sales baseline used
--   - Q7 DECLARE blocks removed; replaced with event_bounds CTE
-- ============================================================


-- ============================================================
-- Query 1: Customer + Event Identification
-- Tool: demand_tools.get_event_details(event_id)
-- Returns: one row per product-location-customer for the event
-- ============================================================

SELECT
    e.id                                            AS event_id,
    e.code                                          AS event_code,
    e.name                                          AS deal_name,
    e.start_date                                    AS start_date,
    e.end_date                                      AS end_date,
    DATEDIFF(day, e.start_date, e.end_date) + 1     AS event_duration_days,
    DATEDIFF(week, e.start_date, e.end_date) + 1    AS event_duration_weeks,
    e.event_lag_days,
    e.warning_days,
    p.id                                            AS product_id,
    p.code                                          AS product_code,
    p.name                                          AS product_name,
    pc.code                                         AS product_class,
    pg.code                                         AS product_group,
    pf.code                                         AS product_family,
    l.id                                            AS location_id,
    l.code                                          AS location_code,
    l.name                                          AS location_name,
    c.id                                            AS customer_id,
    c.code                                          AS customer_code,
    c.name                                          AS customer_name,
    seg.name                                        AS customer_segment,
    eplcx.expected_uplift                           AS planned_uplift,
    eplcx.expected_demand                           AS planned_demand_total,
    eplcx.quantity_ordered,
    eplcx.event_minimum,
    eplcx.is_recal_uplift,
    NULL                                            AS discount_pct
FROM event e
JOIN event_prod_loc_cust_xref   eplcx  ON eplcx.event_id       = e.id
                                       AND eplcx.is_deleted     = 0
JOIN product_location_customer_xref plc ON plc.id              = eplcx.prod_loc_cust_id
                                       AND plc.is_deleted       = 0
JOIN product                    p      ON p.id                  = plc.product_id
JOIN location                   l      ON l.id                  = plc.location_id
JOIN customer                   c      ON c.id                  = plc.customer_id
JOIN product_class              pc     ON pc.id                 = p.product_class_id
JOIN product_group              pg     ON pg.id                 = p.product_primary_group_id
JOIN product_family             pf     ON pf.id                 = p.product_family_id
JOIN segment                    seg    ON seg.id                = c.segment_id
WHERE e.id          = :event_id
  AND e.is_deleted  = 0
ORDER BY p.code, l.code, c.code


-- ============================================================
-- Query 2: Pre-event Baseline Demand
-- Tool: demand_tools.get_baseline_demand(event_id)
-- Returns: single row — baseline_weekly_avg (8-week trailing sales)
--
-- Redesigned 2026-05-15: planned uplift dropped entirely.
-- Scenarios are driven by comparable event actuals (Q4 p25/p50/p75).
-- Already implemented directly in demand_tools.py — no paste needed.
-- ============================================================

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


-- ============================================================
-- Query 3: OOS + Overstock + Service Levels
-- Tool: supply_tools.get_oos_history(event_id)
-- Source: product_location_xref_history
-- Returns one row per change record within ±8 week event window
-- ============================================================

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


-- ============================================================
-- Query 4: Comparable Event Matching + Actual Lift Ratios
-- Tool: demand_tools.find_similar_events(event_id)
-- Finds past completed events: same product_group + customer segment
-- Returns p25/p50/p75 lift and confidence tier
-- ============================================================

WITH anchor AS (
    SELECT DISTINCT
        pg.id    AS product_group_id,
        pg.code  AS product_group_code,
        seg.id   AS customer_segment_id,
        seg.name AS customer_segment_name
    FROM event e
    JOIN event_prod_loc_cust_xref eplcx ON eplcx.event_id = e.id AND eplcx.is_deleted = 0
    JOIN product_location_customer_xref plc ON plc.id = eplcx.prod_loc_cust_id
    JOIN product p ON p.id = plc.product_id
    JOIN product_group pg ON pg.id = p.product_primary_group_id
    JOIN customer c ON c.id = plc.customer_id
    JOIN segment seg ON seg.id = c.segment_id
    WHERE e.id = :event_id AND e.is_deleted = 0
),
comparable_events AS (
    SELECT DISTINCT
        e_comp.id          AS comp_event_id,
        e_comp.code        AS comp_event_code,
        e_comp.name        AS comp_event_name,
        e_comp.start_date  AS comp_start,
        e_comp.end_date    AS comp_end,
        eplcx_comp.prod_loc_cust_id AS comp_plc_id,
        a.product_group_code,
        a.customer_segment_name
    FROM anchor a
    JOIN product p_comp ON p_comp.product_primary_group_id = a.product_group_id
    JOIN product_location_customer_xref plc_comp ON plc_comp.product_id = p_comp.id
    JOIN customer c_comp ON c_comp.id = plc_comp.customer_id
    JOIN segment seg_comp ON seg_comp.id = c_comp.segment_id
        AND seg_comp.name = a.customer_segment_name
    JOIN event_prod_loc_cust_xref eplcx_comp ON eplcx_comp.prod_loc_cust_id = plc_comp.id
        AND eplcx_comp.is_deleted = 0
    JOIN event e_comp ON e_comp.id = eplcx_comp.event_id
        AND e_comp.is_deleted = 0
        AND e_comp.id <> :event_id
        AND e_comp.end_date < GETDATE()
),
comp_lift AS (
    SELECT
        ce.comp_event_id,
        ce.comp_event_code,
        ce.comp_event_name,
        ce.comp_start,
        ce.comp_end,
        ce.product_group_code,
        ce.customer_segment_name,
        AVG(CASE
            WHEN ds.name = 'sales'
             AND dp.period_end <  ce.comp_start
             AND dp.period_end >= DATEADD(week, -8, ce.comp_start)
            THEN unpvt.demand_value
        END) AS pre_event_baseline,
        SUM(CASE
            WHEN ds.name = 'sales'
             AND dp.period_start <= ce.comp_end
             AND dp.period_end   >= ce.comp_start
            THEN unpvt.demand_value
        END) AS actual_sales_during,
        SUM(CASE
            WHEN ds.name = 'event'
             AND dp.period_start <= ce.comp_end
             AND dp.period_end   >= ce.comp_start
            THEN unpvt.demand_value
        END) AS actual_event_uplift,
        SUM(CASE
            WHEN ds.name = 'lostsales'
             AND dp.period_start <= ce.comp_end
             AND dp.period_end   >= ce.comp_start
            THEN unpvt.demand_value
        END) AS lost_sales_during
    FROM comparable_events ce
    JOIN demand_history dh ON dh.prod_loc_cust_id = ce.comp_plc_id
    JOIN demand_signal ds ON ds.id = dh.demand_signal_id
        AND ds.name IN ('sales', 'event', 'lostsales')
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
    JOIN period dp ON dp.period_number = unpvt.period_number
    WHERE dp.period_end   >= DATEADD(week, -8, ce.comp_start)
      AND dp.period_start <= ce.comp_end
    GROUP BY
        ce.comp_event_id, ce.comp_event_code, ce.comp_event_name,
        ce.comp_start, ce.comp_end, ce.product_group_code, ce.customer_segment_name
)
SELECT
    comp_event_id,
    comp_event_code,
    comp_event_name,
    comp_start,
    comp_end,
    product_group_code,
    customer_segment_name,
    pre_event_baseline,
    actual_sales_during,
    actual_event_uplift,
    lost_sales_during,
    actual_sales_during / NULLIF(pre_event_baseline, 0)                                AS actual_lift_ratio,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY actual_sales_during / NULLIF(pre_event_baseline, 0)) OVER () AS lift_p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY actual_sales_during / NULLIF(pre_event_baseline, 0)) OVER () AS lift_p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY actual_sales_during / NULLIF(pre_event_baseline, 0)) OVER () AS lift_p75,
    COUNT(*) OVER ()                                                                    AS comparable_count,
    CASE
        WHEN COUNT(*) OVER () >= 3 THEN 'HIGH'
        WHEN COUNT(*) OVER () >= 1 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS confidence_tier
FROM comp_lift
WHERE pre_event_baseline > 0
ORDER BY actual_lift_ratio DESC


-- ============================================================
-- Query 5: Supply Constraint Snapshot — ATP at T-14
-- Tool: supply_tools.get_inventory_position(event_id)
-- Uses history tables to reconstruct state as of T-14
-- ============================================================

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


-- ============================================================
-- Query 6: Financial Inputs — AS OF T-14
-- Tool: financial_tools.get_financial_inputs(event_id)
-- ============================================================

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


-- ============================================================
-- Query 7: Cannibalization Candidates
-- Tool: demand_tools.get_product_substitutes(event_id)
-- Returns substitute SKUs in same product_class at same location
--
-- DECLARE blocks removed for SQLAlchemy compatibility.
-- @event_id → :event_id; @pre_weeks hardcoded 8;
-- @event_start/@event_end/@min_period/@max_period → event_bounds CTE
-- ============================================================

WITH event_bounds AS (
    SELECT
        e.start_date                  AS event_start,
        e.end_date                    AS event_end,
        MIN(dp.period_number)         AS min_period,
        MAX(dp.period_number)         AS max_period
    FROM event e
    CROSS JOIN period dp
    WHERE e.id = :event_id
      AND dp.period_end   >= DATEADD(week, -8, e.start_date)
      AND dp.period_start <= e.end_date
    GROUP BY e.start_date, e.end_date
),
anchor_class AS (
    SELECT DISTINCT
        p.product_class_id,
        plc.location_id,
        plc.product_id AS promoted_product_id
    FROM event e
    JOIN event_prod_loc_cust_xref eplcx
        ON eplcx.event_id = e.id AND eplcx.is_deleted = 0
    JOIN product_location_customer_xref plc
        ON plc.id = eplcx.prod_loc_cust_id
    JOIN product p ON p.id = plc.product_id
    WHERE e.id = :event_id AND e.is_deleted = 0
),
substitute_plc AS (
    SELECT DISTINCT
        plc_sub.id   AS sub_plc_id,
        p_sub.id     AS sub_product_id,
        p_sub.code   AS sub_product_code,
        p_sub.name   AS sub_product_name,
        pc.code      AS shared_product_class
    FROM anchor_class ac
    JOIN product p_sub
        ON  p_sub.product_class_id = ac.product_class_id
        AND p_sub.id <> ac.promoted_product_id
    JOIN product_class pc ON pc.id = ac.product_class_id
    JOIN product_location_customer_xref plc_sub
        ON  plc_sub.product_id  = p_sub.id
        AND plc_sub.location_id = ac.location_id
),
demand_agg AS (
    SELECT
        sp.sub_product_id,
        sp.sub_product_code,
        sp.sub_product_name,
        sp.shared_product_class,
        AVG(CASE
            WHEN dp.period_start   <  eb.event_start
             AND dp.period_end   >= DATEADD(week, -8, eb.event_start)
            THEN unpvt.demand_value
        END) AS sub_pre_event_baseline,
        SUM(CASE
            WHEN dp.period_start <= eb.event_end
             AND dp.period_end   >= eb.event_start
            THEN unpvt.demand_value
        END) AS sub_actual_sales_during
    FROM substitute_plc sp
    CROSS JOIN event_bounds eb
    JOIN demand_history dh
        ON dh.prod_loc_cust_id = sp.sub_plc_id
    JOIN demand_signal ds
        ON ds.id = dh.demand_signal_id AND ds.name = 'sales'
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
    JOIN period dp ON dp.period_number = unpvt.period_number
    WHERE unpvt.period_number BETWEEN eb.min_period AND eb.max_period
    GROUP BY
        sp.sub_product_id, sp.sub_product_code, sp.sub_product_name, sp.shared_product_class
)
SELECT
    sub_product_id                                          AS sku_id,
    sub_product_code,
    sub_product_name,
    shared_product_class,
    sub_pre_event_baseline                                  AS baseline_demand,
    sub_actual_sales_during,
    CASE
        WHEN sub_pre_event_baseline IS NULL OR sub_pre_event_baseline = 0 THEN -0.20
        ELSE (sub_actual_sales_during / sub_pre_event_baseline) - 1.0
    END AS cannibalization_factor
FROM demand_agg
ORDER BY cannibalization_factor ASC
