from langgraph.graph import StateGraph, START, END

# from .nodes import agent_a_node, agent_b_node
from .state import ChatState, ExperimentState
from dialog_manager import dialog_manager_node

# def _route_after_response(state: ChatState) -> str:
#     """Stop at the configured response limit."""
#     if state["response_count"] >= state["max_responses"]:
#         return "end"

#     return "continue"


# def build_graph_prev(llm):
#     graph = StateGraph(ChatState)

#     # Register nodes. Closures inject the same LLM instance.
#     graph.add_node(
#         "agent_a",
#         lambda state: agent_a_node(state, llm),
#     )

#     graph.add_node(
#         "agent_b",
#         lambda state: agent_b_node(state, llm),
#     )

#     # Define the starting point.
#     graph.add_edge(START, "agent_a")

#     # Route Agent A -> Agent B, or stop.
#     graph.add_conditional_edges(
#         "agent_a",
#         _route_after_response,
#         {
#             "continue": "agent_b",
#             "end": END,
#         },
#     )

#     # Route Agent B -> Agent A, or stop.
#     graph.add_conditional_edges(
#         "agent_b",
#         _route_after_response,
#         {
#             "continue": "agent_a",
#             "end": END,
#         },
#     )

#     return graph.compile()

from manager.node import (
    manager_initialize,
    manager_after_turn,
    route_after_turn,
    manager_finalize,
)

from assessment.nodes import (
    run_baseline_assessment,
    run_followup_assessment,
)

from agent.nodes import (
    user_agent_node,
    character_agent_node,
    update_simulated_state,
)


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

    # Calculate the baseline score and initialize the round counter.
    builder.add_edge(
        "baseline_assessment",
        "manager_initialize",
    )

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
    builder.add_edge(
        "followup_assessment",
        "manager_finalize",
    )
    builder.add_edge("manager_finalize", END)

    return builder.compile()


graph = build_graph()
