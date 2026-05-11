import json
from datetime import datetime, timezone

import anthropic

from casci.prompts.loader import load_prompt
from casci.settings import settings
from casci.state import DemandDecomposition, ScenarioPlanningState
from casci.tools.demand_tools import (
    find_similar_events,
    get_baseline_demand,
    get_product_substitutes,
)

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _map_confidence(tier: str, comparable_count: int) -> float:
    if tier == "HIGH" or comparable_count >= 3:
        return 0.85
    if tier == "MEDIUM" or comparable_count >= 1:
        return 0.55
    return 0.2


def _build_context(baseline: dict, similar: dict, substitutes: list[dict]) -> str:
    comparables_text = "\n".join(
        f"  - Event {i+1}: lift={c.get('lift_actual', 'N/A')}x, "
        f"discount={c.get('discount_pct', 'N/A')}%, "
        f"dip_factor={c.get('post_promo_dip_factor', 'N/A')}, "
        f"segment={c.get('customer_segment', 'N/A')}"
        for i, c in enumerate(similar["comparables"])
    ) or "  None found — using category defaults."

    subs_text = "\n".join(
        f"  - SKU {s['sku_id']}: baseline={s.get('baseline_demand', 'N/A')}, "
        f"cannibalization_factor={s.get('cannibalization_factor', -0.20)}"
        for s in substitutes
    ) or "  None identified."

    return f"""
BASELINE DEMAND
Baseline weekly average: {baseline['baseline_weekly_avg']:.1f} units

LIFT SCENARIOS (pre-computed from comparables)
  Conservative (p25): {similar['lift_p25']}x
  Moderate (p50):     {similar['lift_p50']}x
  Aggressive (p75):   {similar['lift_p75']}x
  Confidence tier:    {similar['confidence_tier']} ({similar['comparable_count']} comparables)

COMPARABLE EVENTS
{comparables_text}

CANNIBALIZATION CANDIDATES
{subs_text}
"""


def demand_decomposition_agent(state: ScenarioPlanningState) -> ScenarioPlanningState:
    event_id = state["event"].deal_id
    ts = datetime.now(timezone.utc).isoformat()

    try:
        baseline   = get_baseline_demand(event_id)
        similar    = find_similar_events(event_id)
        substitutes = get_product_substitutes(event_id)
    except Exception as exc:
        state["errors"].append(f"demand_decomposition: tool error — {exc}")
        state["messages"].append({"agent": "demand_decomposition", "step": "tool_error",
                                  "timestamp": ts, "content": str(exc)})
        return state

    context = _build_context(baseline, similar, substitutes)
    prompt  = load_prompt("demand_decomposition")

    response = client.messages.create(
        model=settings.llm_demand_decomp,
        max_tokens=800,
        system=prompt,
        messages=[{"role": "user", "content": context}],
    )

    try:
        parsed = json.loads(response.content[0].text)
    except json.JSONDecodeError as exc:
        state["errors"].append(f"demand_decomposition: LLM returned invalid JSON — {exc}")
        return state

    state["demand_decomposition"] = DemandDecomposition(
        baseline_weekly_demand=baseline["baseline_weekly_avg"],
        historical_similar_events=similar["comparables"],
        lift_scenarios={
            "conservative": similar["lift_p25"],
            "moderate":     similar["lift_p50"],
            "aggressive":   similar["lift_p75"],
        },
        post_promo_dip_factor=float(parsed.get("post_promo_dip_factor", 0.65)),
        cannibalization_impact={
            s["sku_id"]: float(s.get("cannibalization_factor", -0.20))
            for s in substitutes
        },
        confidence=_map_confidence(similar["confidence_tier"], similar["comparable_count"]),
        conservative_rationale=parsed.get("conservative_rationale", ""),
        moderate_rationale=parsed.get("moderate_rationale", ""),
        aggressive_rationale=parsed.get("aggressive_rationale", ""),
    )

    state["messages"].append({
        "agent": "demand_decomposition",
        "step": "complete",
        "timestamp": ts,
        "content": f"confidence={state['demand_decomposition'].confidence}, "
                   f"comparables={similar['comparable_count']}",
    })
    state["current_step"] = "demand_decomposition_complete"
    return state
