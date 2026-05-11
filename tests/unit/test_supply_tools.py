"""Unit tests for supply constraint tool functions."""
from unittest.mock import patch
import pytest
from casci.tools.supply_tools import get_inventory_position


@patch("casci.tools.supply_tools.execute_query")
def test_get_inventory_position_returns_correct_atp(mock_query):
    mock_query.return_value = [{
        "atp": 1450.0, "lead_time_days": 10, "lead_time_feasible": True,
        "moq": 500.0, "max_order_qty": 5000.0, "sourcing_notes": "",
    }]
    result = get_inventory_position(event_id=41)
    assert result["available_to_promise"] == 1450.0
    assert result["is_prestage_feasible"] is True


@patch("casci.tools.supply_tools.execute_query")
def test_get_inventory_position_raises_on_no_data(mock_query):
    mock_query.return_value = []
    with pytest.raises(ValueError, match="No inventory snapshot"):
        get_inventory_position(event_id=99)
