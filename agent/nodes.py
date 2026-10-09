from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .prompts import AGENT_A_PROMPT, AGENT_B_PROMPT
from .state import ChatState


def _run_agent(state: ChatState, llm, name: str, prompt: str):
    # Convert the conversation history into a readable transcript.
    transcript = []

    for message in state["messages"]:
        speaker = getattr(message, "name", None)

        if not speaker:
            speaker = (
                "User"
                if isinstance(message, HumanMessage)
                else "Assistant"
            )

        transcript.append(
            f"{speaker}: {message.content}"
        )

    conversation = "\n\n".join(transcript)

    # Give the model a clear instruction to produce the next turn.
    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=(
            f"Discussion topic: {state['topic']}\n\n"
            f"Conversation so far:\n{conversation}\n\n"
            f"You are {name}. Continue the conversation as this participant. "
            "Reply directly to the last speaker using natural first-person dialogue. "
            "Address that speaker as 'you' when appropriate. "
            "Never discuss either participant in the third person. "
            "Do not mention Agent A or Agent B by name in your response. "
            "Do not repeat the transcript or include speaker labels."
        )),
    ])

    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            block["text"]
            for block in content
            if isinstance(block, dict)
            and isinstance(block.get("text"), str)
        )

    if not isinstance(content, str) or not content.strip():
        metadata = response.response_metadata

        raise RuntimeError(
            f"{name} returned an empty response. "
            f"Metadata: {metadata}"
        )

    print(
        f"[DEBUG] {name}: "
        f"{len(content)} characters generated"
    )

    return {
        "messages": [
            AIMessage(
                content=content.strip(),
                name=name,
            )
        ],
        "response_count": state["response_count"] + 1,
    }


def agent_a_node(state: ChatState, llm):
    return _run_agent(
        state, llm, "Agent A", AGENT_A_PROMPT
    )


def agent_b_node(state: ChatState, llm):
    return _run_agent(
        state, llm, "Agent B", AGENT_B_PROMPT
    )