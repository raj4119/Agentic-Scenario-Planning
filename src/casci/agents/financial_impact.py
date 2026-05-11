from datetime import datetime, timezone

import anthropic

from casci.prompts.loader import load_prompt
from casci.settings import settings
from casci.state import FinancialImpact, ScenarioPlanningState
from casci.tools.financial_tools import calculate_net_impact, get_financial_inputs

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def financial_impact_agent(state: ScenarioPlanningState) -> ScenarioPlanningState:
    event_id = state["event"].deal_id
    ts = datetime.now(timezone.utc).isoformat()

    try:
        fin = get_financial_inputs(event_id)
    except Exception as exc:
        state["errors"].append(f"financial_impact: tool error — {exc}")
        return state

    confidence = state["demand_decomposition"].confidence
    ci_pct = round((1 - confidence) * 30, 1)   # max ±30% at zero confidence

    impacts = []
    for scenario in state["scenarios"]:
        calcs = calculate_net_impact(scenario, fin)
        impacts.append(FinancialImpact(
            scenario_name=scenario.name,
            projected_revenue=calcs["projected_revenue"],
            carrying_cost=calcs["carrying_cost"],
            expected_stockout_cost=calcs["expected_stockout_cost"],
            net_financial_impact=calcs["net_financial_impact"],
            confidence_interval_pct=ci_pct,
        ))

    state["financial_impacts"] = impacts

    # LLM narration — summarises the numbers, does not generate them
    impacts_text = "\n".join(
        f"  {fi.scenario_name}: revenue=${fi.projected_revenue:,.0f}, "
        f"carrying=${fi.carrying_cost:,.0f}, stockout=${fi.expected_stockout_cost:,.0f}, "
        f"net=${fi.net_financial_impact:,.0f}, CI=±{fi.confidence_interval_pct}%"
        for fi in impacts
    )
    feasible_names = {s.name for s in state["scenarios"] if s.is_feasible}
    prefix = "Given limited historical data, " if confidence < settings.confidence_low_threshold else ""

    prompt = load_prompt("financial_impact")
    response = client.messages.create(
        model=settings.llm_narration,
        max_tokens=150,
        messages=[{
            "role": "user",
            "content": (
                f"{prefix}Here are the financial impacts for three scenarios. "
                f"Feasible scenarios: {feasible_names}.\n\n{impacts_text}"
            ),
        }],
        system=prompt,
    )

    state["messages"].append({
        "agent": "financial_impact",
        "step": "complete",
        "timestamp": ts,
        "content": response.content[0].text.strip(),
    })
    state["current_step"] = "financial_impact_complete"
    return state
