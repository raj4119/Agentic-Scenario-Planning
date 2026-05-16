"""Unit tests for demand tool functions — uses mocked DB responses."""
from unittest.mock import patch
import pytest
from casci.tools.demand_tools import find_similar_events, get_baseline_demand


@patch("casci.tools.demand_tools.execute_query")
def test_find_similar_events_returns_lift_percentiles(mock_query):
    mock_query.return_value = [{
        "lift_p25": 2.0, "lift_p50": 2.5, "lift_p75": 3.1,
        "confidence_tier": "HIGH", "comparable_count": 4,
        "lift_actual": 2.5, "discount_pct": 0.30,
    }]
    result = find_similar_events(event_id=41)
    assert result["lift_p25"] < result["lift_p50"] < result["lift_p75"]
    assert result["confidence_tier"] == "HIGH"
    assert result["comparable_count"] == 4


@patch("casci.tools.demand_tools.execute_query")
def test_find_similar_events_no_comparables_returns_defaults(mock_query):
    mock_query.return_value = []
    result = find_similar_events(event_id=99)
    assert result["confidence_tier"] == "LOW"
    assert result["comparable_count"] == 0
    assert result["lift_p25"] < result["lift_p50"] < result["lift_p75"]


@patch("casci.tools.demand_tools.execute_query")
def test_get_baseline_demand_returns_avg(mock_query):
    mock_query.return_value = [{"baseline_weekly_avg": 110.0}]
    result = get_baseline_demand(event_id=41)
    assert result["baseline_weekly_avg"] == pytest.approx(110.0)


@patch("casci.tools.demand_tools.execute_query")
def test_get_baseline_demand_raises_on_no_data(mock_query):
    mock_query.return_value = []
    with pytest.raises(ValueError, match="No baseline demand found"):
        get_baseline_demand(event_id=99)
