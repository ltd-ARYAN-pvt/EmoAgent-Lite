from langgraph.graph import StateGraph, START, END
from .state import ExperimentState
from dialog_manager import dialog_manager_node

from manager.node import (
    manager_initialize,
    manager_after_turn,
    route_after_turn,
    manager_finalize,
)

from assessment import (
    run_baseline_assessment,
    run_followup_assessment,
    run_followup_pdi_assessment,
    run_baseline_pdi_assessment
)

from agent.nodes import (
    user_agent_node,
    character_agent_node,
    update_simulated_state,
)

def route_after_baseline_assessment(state: ExperimentState) -> str:
    enabled = state.get("enabled_assessments", ["phq9"])
    return "pdi" if "pdi" in enabled else "initialize"


def route_after_followup_assessment(state: ExperimentState) -> str:
    enabled = state.get("enabled_assessments", ["phq9"])
    return "pdi" if "pdi" in enabled else "finalize"


def build_graph():
    builder = StateGraph(ExperimentState)

    # Assessment nodes
    builder.add_node(
        "baseline_assessment",
        run_baseline_assessment,
    )
    builder.add_node(
        "followup_assessment",
        run_followup_assessment,
    )
    builder.add_node(
        "baseline_pdi_assessment",
        run_baseline_pdi_assessment,
    )
    builder.add_node(
        "followup_pdi_assessment",
        run_followup_pdi_assessment,
    )

    # Manager nodes
    builder.add_node("manager_initialize", manager_initialize)
    builder.add_node("manager_after_turn", manager_after_turn)
    builder.add_node("manager_finalize", manager_finalize)
    builder.add_node("dialog_manager", dialog_manager_node)

    # Conversation nodes
    builder.add_node("user_agent", user_agent_node)
    builder.add_node("character_agent", character_agent_node)
    builder.add_node("update_simulated_state", update_simulated_state)

    # Start by collecting the baseline responses.
    builder.add_edge(START, "baseline_assessment")

    builder.add_conditional_edges(
        "baseline_assessment",
        route_after_baseline_assessment,
        {
            "pdi": "baseline_pdi_assessment",
            "initialize": "manager_initialize",
        },
    )
    builder.add_edge("baseline_pdi_assessment", "manager_initialize")

    builder.add_edge("manager_initialize", "dialog_manager")
    builder.add_edge("dialog_manager", "user_agent")

    builder.add_edge("user_agent", "character_agent")

    # Update the simulated persona state after the exchange.
    builder.add_edge(
        "character_agent",
        "update_simulated_state",
    )

    # Increment the completed conversation round.
    builder.add_edge(
        "update_simulated_state",
        "manager_after_turn",
    )

    # Continue chatting or proceed to the follow-up assessment.
    builder.add_conditional_edges(
        "manager_after_turn",
        route_after_turn,
        {
            "continue": "dialog_manager",
            "finish": "followup_assessment",
        },
    )

    # Calculate and compare the final scores, then produce the result.
    builder.add_conditional_edges(
        "followup_assessment",
        route_after_followup_assessment,
        {
            "pdi": "followup_pdi_assessment",
            "finalize": "manager_finalize",
        },
    )
    builder.add_edge("followup_pdi_assessment", "manager_finalize")
    builder.add_edge("manager_finalize", END)

    return builder.compile()


graph = build_graph()
