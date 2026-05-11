import json
import re
from datetime import datetime, timezone

import anthropic

from casci.prompts.loader import load_prompt
from casci.settings import settings
from casci.state import Scenario, ScenarioPlanningState

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_EXPECTED_NAMES = {"Conservative", "Moderate", "Aggressive"}


def _build_prompt(state: ScenarioPlanningState) -> str:
    dd = state["demand_decomposition"]
    sc = state["supply_constraints"]

    template = load_prompt("scenario_generator")
    return template.format(
        lift_conservative=dd.lift_scenarios["conservative"],
        lift_moderate=dd.lift_scenarios["moderate"],
        lift_aggressive=dd.lift_scenarios["aggressive"],
        baseline_weekly_demand=dd.baseline_weekly_demand,
        event_duration_weeks=state["event"].duration_weeks,
        supply_constraints_summary=sc.constraint_notes,
    )


def _parse_scenarios(raw: str) -> list[Scenario]:
    """Strip <thinking> block and parse JSON array of scenarios."""
    clean = re.sub(r"<thinking>.*?</thinking>", "", raw, flags=re.DOTALL).strip()
    data  = json.loads(clean)
    return [
        Scenario(
            name=s["name"],
            lift_assumption=float(s["lift_assumption"]),
            pre_stage_quantity=float(s["pre_stage_quantity"]),
            order_timing_weeks_before=int(s["order_timing_weeks_before"]),
            service_level_target=float(s["service_level_target"]),
            post_event_rundown_weeks=int(s["post_event_rundown_weeks"]),
            week_by_week_demand=[float(d) for d in s["week_by_week_demand"]],
            narrative=s["narrative"],
            is_feasible=bool(s["is_feasible"]),
        )
        for s in data
    ]


def _validate(scenarios: list[Scenario], state: ScenarioPlanningState) -> list[str]:
    errors = []
    if len(scenarios) != 3:
        errors.append(f"Expected 3 scenarios, got {len(scenarios)}")
    names = {s.name for s in scenarios}
    if names != _EXPECTED_NAMES:
        errors.append(f"Unexpected scenario names: {names}")
    lifts = sorted(s.lift_assumption for s in scenarios)
    if lifts[-1] - lifts[0] < settings.min_scenario_lift_spread:
        errors.append(
            f"Scenarios not sufficiently differentiated: spread={lifts[-1]-lifts[0]:.2f} "
            f"(min={settings.min_scenario_lift_spread})"
        )
    for s in scenarios:
        if not (settings.min_lift_assumption <= s.lift_assumption <= settings.max_lift_assumption):
            errors.append(f"{s.name}: lift_assumption {s.lift_assumption} out of range")
        if not (0.85 <= s.service_level_target <= 1.0):
            errors.append(f"{s.name}: service_level_target {s.service_level_target} out of range")
    return errors


def scenario_generator_agent(state: ScenarioPlanningState) -> ScenarioPlanningState:
    ts = datetime.now(timezone.utc).isoformat()
    prompt = _build_prompt(state)

    for attempt in range(1, settings.llm_max_retries + 1):
        response = client.messages.create(
            model=settings.llm_scenario_generator,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            scenarios = _parse_scenarios(response.content[0].text)
        except (json.JSONDecodeError, KeyError) as exc:
            state["errors"].append(f"scenario_generator: parse error on attempt {attempt} — {exc}")
            continue

        validation_errors = _validate(scenarios, state)
        if not validation_errors:
            state["scenarios"] = scenarios
            state["messages"].append({
                "agent": "scenario_generator",
                "step": "complete",
                "timestamp": ts,
                "content": f"attempt={attempt}, scenarios={[s.name for s in scenarios]}",
            })
            state["current_step"] = "scenario_generator_complete"
            return state

        # Retry with differentiation instruction appended
        prompt += (
            f"\n\nPREVIOUS ATTEMPT FAILED VALIDATION:\n"
            + "\n".join(f"  - {e}" for e in validation_errors)
            + "\n\nPlease fix these issues and regenerate."
        )

    state["errors"].append("scenario_generator: failed after max retries")
    return state
