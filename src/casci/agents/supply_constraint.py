from datetime import datetime, timezone

import anthropic

from casci.settings import settings
from casci.state import ScenarioPlanningState, SupplyConstraints
from casci.tools.supply_tools import get_inventory_position, get_oos_history

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _check_feasibility(
    lift_scenarios: dict[str, float],
    baseline: float,
    duration_weeks: int,
    inv: dict,
) -> list[dict]:
    results = []
    for name, lift in lift_scenarios.items():
        required = baseline * lift * duration_weeks
        orderable = inv["max_order_qty"] if inv["is_prestage_feasible"] else 0.0
        is_feasible = (inv["available_to_promise"] + orderable) >= required
        results.append({
            "scenario": name,
            "required_units": round(required, 1),
            "available_to_promise": inv["available_to_promise"],
            "is_feasible": is_feasible,
        })
    return results


def _generate_constraint_summary(inv: dict, feasibility: list[dict]) -> str:
    infeasible = [f["scenario"] for f in feasibility if not f["is_feasible"]]
    feasible   = [f["scenario"] for f in feasibility if f["is_feasible"]]

    context = (
        f"ATP: {inv['available_to_promise']} units. "
        f"Lead time: {inv['lead_time_days']} days. "
        f"Pre-stage feasible: {inv['is_prestage_feasible']}. "
        f"Max order: {inv['max_order_qty']} units. "
        f"Feasible scenarios: {feasible}. "
        f"Infeasible scenarios: {infeasible}. "
        f"Notes: {inv['sourcing_notes']}"
    )

    response = client.messages.create(
        model=settings.llm_narration,
        max_tokens=150,
        messages=[{
            "role": "user",
            "content": (
                "Summarise these supply constraints in 2 plain-language sentences "
                "for a demand planner. Be specific about which scenarios are at risk "
                "and why.\n\n" + context
            ),
        }],
    )
    return response.content[0].text.strip()


def supply_constraint_agent(state: ScenarioPlanningState) -> ScenarioPlanningState:
    event_id = state["event"].deal_id
    ts = datetime.now(timezone.utc).isoformat()

    try:
        inv = get_inventory_position(event_id)
        get_oos_history(event_id)           # surfaced in state messages for observability
    except Exception as exc:
        state["errors"].append(f"supply_constraint: tool error — {exc}")
        state["messages"].append({"agent": "supply_constraint", "step": "tool_error",
                                  "timestamp": ts, "content": str(exc)})
        return state

    lift_scenarios = state["demand_decomposition"].lift_scenarios
    baseline       = state["demand_decomposition"].baseline_weekly_demand
    duration       = state["event"].duration_weeks

    feasibility = _check_feasibility(lift_scenarios, baseline, duration, inv)
    summary     = _generate_constraint_summary(inv, feasibility)

    state["supply_constraints"] = SupplyConstraints(
        available_to_promise=inv["available_to_promise"],
        supplier_lead_time_days=inv["lead_time_days"],
        min_order_qty=inv["min_order_qty"],
        max_order_qty=inv["max_order_qty"],
        is_fulfillable=any(f["is_feasible"] for f in feasibility),
        scenario_feasibility=feasibility,
        constraint_notes=summary,
    )

    state["messages"].append({
        "agent": "supply_constraint",
        "step": "complete",
        "timestamp": ts,
        "content": f"atp={inv['available_to_promise']}, "
                   f"feasible_scenarios={[f['scenario'] for f in feasibility if f['is_feasible']]}",
    })
    state["current_step"] = "supply_constraint_complete"
    return state
