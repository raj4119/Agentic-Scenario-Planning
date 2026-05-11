from langgraph.graph import END, StateGraph

from casci.agents.demand_decomposition import demand_decomposition_agent
from casci.agents.financial_impact import financial_impact_agent
from casci.agents.orchestrator import orchestrator_agent, route_from_orchestrator
from casci.agents.scenario_generator import scenario_generator_agent
from casci.agents.supply_constraint import supply_constraint_agent
from casci.state import PromotionalEvent, ScenarioPlanningState


def build_graph():
    graph = StateGraph(ScenarioPlanningState)

    graph.add_node("orchestrator",         orchestrator_agent)
    graph.add_node("demand_decomposition", demand_decomposition_agent)
    graph.add_node("supply_constraint",    supply_constraint_agent)
    graph.add_node("scenario_generator",   scenario_generator_agent)
    graph.add_node("financial_impact",     financial_impact_agent)

    graph.set_entry_point("orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "run_analysis": ["demand_decomposition", "supply_constraint"],
            "error": END,
        },
    )

    # Both parallel agents must finish before scenario generator starts
    graph.add_edge("demand_decomposition", "scenario_generator")
    graph.add_edge("supply_constraint",    "scenario_generator")
    graph.add_edge("scenario_generator",   "financial_impact")
    graph.add_edge("financial_impact",     END)

    return graph.compile()


def run_scenario_planning(event: PromotionalEvent) -> ScenarioPlanningState:
    """Main entry point. Pass a PromotionalEvent, get back the full state."""
    graph = build_graph()
    initial_state: ScenarioPlanningState = {
        "event": event,
        "demand_decomposition": None,
        "supply_constraints": None,
        "scenarios": None,
        "financial_impacts": None,
        "current_step": "start",
        "errors": [],
        "planner_selection": None,
        "messages": [],
    }
    return graph.invoke(initial_state)
