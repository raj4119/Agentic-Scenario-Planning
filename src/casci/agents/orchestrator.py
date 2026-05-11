from casci.state import ScenarioPlanningState
from datetime import datetime, timezone


def orchestrator_agent(state: ScenarioPlanningState) -> ScenarioPlanningState:
    """Entry point. Validates the event payload and initialises the pipeline."""
    state["messages"].append({
        "agent": "orchestrator",
        "step": "entry",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "content": f"Pipeline started for event_id={state['event'].deal_id if state['event'] else None}",
    })

    if state["event"] is None:
        state["errors"].append("orchestrator: event payload is None — cannot proceed")

    state["current_step"] = "orchestrator_complete"
    return state


def route_from_orchestrator(state: ScenarioPlanningState) -> str:
    if state["errors"]:
        return "error"
    return "run_analysis"
