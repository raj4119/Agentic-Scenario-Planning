from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, TypedDict


@dataclass
class PromotionalEvent:
    deal_id: int
    deal_name: str
    sku_id: str
    customer_id: str
    location_id: str
    product_group: str
    product_class: str
    customer_segment: str
    start_date: str        # ISO 8601 "YYYY-MM-DD"
    end_date: str
    duration_weeks: int
    discount_pct: float    # e.g. 0.30 for 30%
    planned_uplift: float  # from event_prod_loc_cust_uplift


@dataclass
class DemandDecomposition:
    baseline_weekly_demand: float
    historical_similar_events: list[dict]
    lift_scenarios: dict[str, float]       # {"conservative": 2.1, "moderate": 2.5, "aggressive": 3.0}
    post_promo_dip_factor: float           # e.g. 0.62 = demand drops to 62% of baseline
    cannibalization_impact: dict[str, float]  # {sku_id: factor}
    confidence: float                      # 0.0–1.0
    conservative_rationale: str
    moderate_rationale: str
    aggressive_rationale: str


@dataclass
class SupplyConstraints:
    available_to_promise: float
    supplier_lead_time_days: int
    min_order_qty: float
    max_order_qty: float
    is_fulfillable: bool
    scenario_feasibility: list[dict]       # [{"scenario": "Conservative", "required_units": X, "is_feasible": True}]
    constraint_notes: str                  # LLM-generated plain-language summary


@dataclass
class Scenario:
    name: str                              # "Conservative" | "Moderate" | "Aggressive"
    lift_assumption: float
    pre_stage_quantity: float
    order_timing_weeks_before: int
    service_level_target: float            # 0.85–1.0
    post_event_rundown_weeks: int
    week_by_week_demand: list[float]
    narrative: str
    is_feasible: bool


@dataclass
class FinancialImpact:
    scenario_name: str
    projected_revenue: float
    carrying_cost: float
    expected_stockout_cost: float
    net_financial_impact: float
    confidence_interval_pct: float         # e.g. 15.0 means ±15%


class ScenarioPlanningState(TypedDict):
    # Input
    event: Optional[PromotionalEvent]

    # Agent outputs
    demand_decomposition: Optional[DemandDecomposition]
    supply_constraints: Optional[SupplyConstraints]
    scenarios: Optional[list[Scenario]]
    financial_impacts: Optional[list[FinancialImpact]]

    # Control
    current_step: str
    errors: list[str]
    planner_selection: Optional[str]
    messages: list[dict]
