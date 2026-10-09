
from langgraph.graph import StateGraph, START, END

from .nodes import agent_a_node, agent_b_node
from .state import ChatState


def _route_after_response(state: ChatState) -> str:
    """Stop at the configured response limit."""
    if state["response_count"] >= state["max_responses"]:
        return "end"

    return "continue"


def build_graph(llm):
    graph = StateGraph(ChatState)

    # Register nodes. Closures inject the same LLM instance.
    graph.add_node(
        "agent_a",
        lambda state: agent_a_node(state, llm),
    )

    graph.add_node(
        "agent_b",
        lambda state: agent_b_node(state, llm),
    )

    # Define the starting point.
    graph.add_edge(START, "agent_a")

    # Route Agent A -> Agent B, or stop.
    graph.add_conditional_edges(
        "agent_a",
        _route_after_response,
        {
            "continue": "agent_b",
            "end": END,
        },
    )

    # Route Agent B -> Agent A, or stop.
    graph.add_conditional_edges(
        "agent_b",
        _route_after_response,
        {
            "continue": "agent_a",
            "end": END,
        },
    )

    return graph.compile()