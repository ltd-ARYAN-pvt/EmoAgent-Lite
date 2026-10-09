from langchain_core.messages import AIMessage, SystemMessage

from .prompts import AGENT_A_PROMPT, AGENT_B_PROMPT
from .state import ChatState


def _run_agent(state: ChatState, llm, name: str, prompt: str):
    """Generate one reply and return only the state updates."""

    response = llm.invoke(
        [
            SystemMessage(content=prompt),
            *state["messages"],
        ]
    )

    return {
        "messages": [
            AIMessage(
                content=response.content,
                name=name,
            )
        ],
        "response_count": state["response_count"] + 1,
    }


def agent_a_node(state: ChatState, llm):
    return _run_agent(
        state=state,
        llm=llm,
        name="Agent A",
        prompt=AGENT_A_PROMPT,
    )


def agent_b_node(state: ChatState, llm):
    return _run_agent(
        state=state,
        llm=llm,
        name="Agent B",
        prompt=AGENT_B_PROMPT,
    )