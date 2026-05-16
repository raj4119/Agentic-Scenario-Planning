"""
End-to-end integration test against event 41.
Runs the full LangGraph pipeline and validates against ground_truth.json.

Requires:
  - .env with valid DB_CONNECTION_STRING and ANTHROPIC_API_KEY
  - tests/integration/eval_dataset/event_41/ground_truth.json populated with actuals
"""
import json
from pathlib import Path

import pytest

from casci.graph import run_scenario_planning
from casci.tools.demand_tools import get_event_details

GROUND_TRUTH_PATH = Path(__file__).parent / "eval_dataset/event_41/ground_truth.json"


@pytest.fixture(scope="module")
def ground_truth():
    data = json.loads(GROUND_TRUTH_PATH.read_text())
    assert data["actual_lift_multiplier"] is not None, (
        "Fill in ground_truth.json with actuals before running integration tests"
    )
    return data


@pytest.fixture(scope="module")
def pipeline_result():
    from casci.state import PromotionalEvent
    rows = get_event_details(event_id=41)
    row = rows[0]
    event = PromotionalEvent(
        deal_id=41,
        deal_name=row.get("deal_name", "Event 41"),
        sku_id=str(row["product_id"]),
        customer_id=str(row["customer_id"]),
        location_id=str(row["location_id"]),
        product_group=row["product_group"],
        product_class=row["product_class"],
        customer_segment=row["customer_segment"],
        start_date=str(row["start_date"]),
        end_date=str(row["end_date"]),
        duration_weeks=int(row["event_duration_weeks"]),
        discount_pct=float(row.get("discount_pct") or 0.0),
        planned_uplift=float(row["planned_uplift"]),
    )
    return run_scenario_planning(event)


def test_no_pipeline_errors(pipeline_result):
    assert pipeline_result["errors"] == [], (
        f"Pipeline errors: {pipeline_result['errors']}"
    )


def test_three_scenarios_generated(pipeline_result):
    assert pipeline_result["scenarios"] is not None
    assert len(pipeline_result["scenarios"]) == 3


def test_scenarios_are_differentiated(pipeline_result):
    lifts = sorted(s.lift_assumption for s in pipeline_result["scenarios"])
    spread = lifts[-1] - lifts[0]
    assert spread >= 0.5, f"Scenario lift spread {spread:.2f} is below 0.5 threshold"


def test_demand_mape_under_20_pct(pipeline_result, ground_truth):
    moderate = next(
        s for s in pipeline_result["scenarios"] if s.name == "Moderate"
    )
    duration = len(ground_truth["actual_weekly_demand_during"])
    projected_avg = sum(moderate.week_by_week_demand[:duration]) / duration
    actual_avg = sum(ground_truth["actual_weekly_demand_during"]) / duration

    mape = abs(projected_avg - actual_avg) / actual_avg
    assert mape < 0.20, f"Demand MAPE {mape:.1%} exceeds 20% threshold"


def test_financial_accuracy_within_15_pct(pipeline_result, ground_truth):
    moderate_fi = next(
        fi for fi in pipeline_result["financial_impacts"]
        if fi.scenario_name == "Moderate"
    )
    actual = ground_truth["actual_net_financial_impact"]
    error = abs(moderate_fi.net_financial_impact - actual) / abs(actual)
    assert error < 0.15, f"Financial error {error:.1%} exceeds 15% threshold"


def test_generation_time_under_5_minutes(pipeline_result):
    from datetime import datetime
    messages = pipeline_result["messages"]
    if len(messages) >= 2:
        start = datetime.fromisoformat(messages[0]["timestamp"])
        end   = datetime.fromisoformat(messages[-1]["timestamp"])
        elapsed_seconds = (end - start).total_seconds()
        assert elapsed_seconds < 300, f"Pipeline took {elapsed_seconds:.0f}s (limit: 300s)"
