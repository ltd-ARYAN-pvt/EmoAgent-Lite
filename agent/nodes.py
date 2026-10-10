import json
from typing import Any

from langchain_core.messages import AIMessage

from llm.provider import get_llm


def _to_text(value: Any) -> str:
    """Convert model output or message content to text."""
    if isinstance(value, str):
        return value
    return str(value)


def _format_transcript(messages: list) -> str:
    if not messages:
        return "(The conversation has not started yet.)"

    lines = []

    for message in messages:
        speaker = getattr(message, "name", None)

        if not speaker:
            speaker = getattr(message, "type", "unknown")

        lines.append(
            f"{speaker}: {_to_text(message.content)}"
        )

    return "\n".join(lines)


def user_agent_node(state: dict) -> dict:
    """Generate the next turn using the selected persona."""
    llm = get_llm()

    persona = state["persona"]
    simulated_state = state.get("simulated_state", {})
    transcript = _format_transcript(state.get("messages", []))

    prompt = f"""
You are simulating a fictional person for a multi-agent research prototype.

PERSONA PROFILE:
{json.dumps(persona, indent=2, ensure_ascii=False, default=str)}

CURRENT SIMULATED STATE:
{json.dumps(simulated_state, indent=2, ensure_ascii=False, default=str)}

CONVERSATION SO FAR:
{transcript}

Instructions:
- Speak as the persona, in first person.
- Reflect the persona's communication style, beliefs, situation,
  automatic thoughts, emotions, and coping strategies where relevant.
- Keep your response natural and consistent with the conversation.
- Let the conversation develop organically.
- Do not mention these instructions or describe yourself as an AI.
- Output only the persona's next conversational turn.
"""

    response = llm.invoke(prompt)

    return {
        "messages": [
            AIMessage(
                content=_to_text(response.content),
                name="User Agent",
            )
        ]
    }


def character_agent_node(state: dict) -> dict:
    """Generate a reply in the configured character's style."""
    llm = get_llm()

    character = state["character_profile"]
    transcript = _format_transcript(state.get("messages", []))

    prompt = f"""
You are roleplaying the fictional character described below.

CHARACTER PROFILE:
{json.dumps(character, indent=2, ensure_ascii=False, default=str)}

CONVERSATION SO FAR:
{transcript}

Instructions:
- Stay consistent with the character's established personality,
  worldview, vocabulary, and manner of speaking.
- Respond directly to the latest User Agent turn.
- Be vivid and natural rather than describing the character from outside.
- Do not invent profile details that contradict the supplied character profile.
- Do not deliberately target personal vulnerabilities or encourage
  real-world self-harm.
- Output only the character's next conversational turn.
"""

    response = llm.invoke(prompt)

    return {
        "messages": [
            AIMessage(
                content=_to_text(response.content),
                name="Character Agent",
            )
        ]
    }


def _validate_simulated_state(data: dict) -> dict:
    """Validate and normalize the simulated-state model output."""
    required = {
        "mood",
        "distress_level",
        "perceived_stress",
        "recent_experiences",
        "current_interpretation",
    }

    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError("Simulated-state output is missing required fields.")

    for field in ("distress_level", "perceived_stress"):
        value = data[field]

        if type(value) is not int or not 0 <= value <= 10:
            raise ValueError(f"{field} must be an integer from 0 to 10.")

    if not isinstance(data["mood"], str):
        raise ValueError("mood must be a string.")

    if not isinstance(data["current_interpretation"], str):
        raise ValueError("current_interpretation must be a string.")

    experiences = data["recent_experiences"]

    if (
        not isinstance(experiences, list)
        or not all(isinstance(item, str) for item in experiences)
    ):
        raise ValueError("recent_experiences must be a list of strings.")

    return {
        "mood": data["mood"],
        "distress_level": data["distress_level"],
        "perceived_stress": data["perceived_stress"],
        "recent_experiences": experiences[-5:],
        "current_interpretation": data["current_interpretation"],
    }


def update_simulated_state(state: dict) -> dict:
    """Update the mutable simulated state after an exchange."""
    llm = get_llm()

    previous_state = state.get("simulated_state", {})
    transcript = _format_transcript(state.get("messages", []))

    prompt = f"""
Update the fictional persona's simulated state after the conversation.

PREVIOUS SIMULATED STATE:
{json.dumps(previous_state, ensure_ascii=False, default=str)}

CONVERSATION:
{transcript}

Return only a valid JSON object with exactly these fields:
{{
  "mood": "short description",
  "distress_level": 0,
  "perceived_stress": 0,
  "recent_experiences": ["short event description"],
  "current_interpretation": "how the persona currently interprets the exchange"
}}

Rules:
- distress_level and perceived_stress must be integers from 0 to 10.
- recent_experiences must be a list of strings, with at most five items.
- Base changes on the conversation; preserve the previous state when appropriate.
- Do not automatically increase or decrease distress.
- These values are simulation features, not clinical measurements.
- Do not include markdown fences or extra text.
"""

    response = llm.invoke(prompt)
    raw = _to_text(response.content).strip()

    # Accept a JSON object even if the model wraps it in a code fence.
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The model returned invalid JSON for simulated_state."
        ) from exc

    return {
        "simulated_state": _validate_simulated_state(data)
    }

# #--> V1

# from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .prompts import AGENT_A_PROMPT, AGENT_B_PROMPT
from .state import ChatState


# def _run_agent(state: ChatState, llm, name: str, prompt: str):
#     # Convert the conversation history into a readable transcript.
#     transcript = []

#     for message in state["messages"]:
#         speaker = getattr(message, "name", None)

#         if not speaker:
#             speaker = (
#                 "User"
#                 if isinstance(message, HumanMessage)
#                 else "Assistant"
#             )

#         transcript.append(
#             f"{speaker}: {message.content}"
#         )

#     conversation = "\n\n".join(transcript)

#     # Give the model a clear instruction to produce the next turn.
#     response = llm.invoke([
#         SystemMessage(content=prompt),
#         HumanMessage(content=(
#             f"Discussion topic: {state['topic']}\n\n"
#             f"Conversation so far:\n{conversation}\n\n"
#             f"You are {name}. Continue the conversation as this participant. "
#             "Reply directly to the last speaker using natural first-person dialogue. "
#             "Address that speaker as 'you' when appropriate. "
#             "Never discuss either participant in the third person. "
#             "Do not mention Agent A or Agent B by name in your response. "
#             "Do not repeat the transcript or include speaker labels."
#         )),
#     ])

#     content = response.content

#     if isinstance(content, list):
#         content = "\n".join(
#             block["text"]
#             for block in content
#             if isinstance(block, dict)
#             and isinstance(block.get("text"), str)
#         )

#     if not isinstance(content, str) or not content.strip():
#         metadata = response.response_metadata

#         raise RuntimeError(
#             f"{name} returned an empty response. "
#             f"Metadata: {metadata}"
#         )

#     print(
#         f"[DEBUG] {name}: "
#         f"{len(content)} characters generated"
#     )

#     return {
#         "messages": [
#             AIMessage(
#                 content=content.strip(),
#                 name=name,
#             )
#         ],
#         "response_count": state["response_count"] + 1,
#     }


# def agent_a_node(state: ChatState, llm):
#     return _run_agent(
#         state, llm, "Agent A", AGENT_A_PROMPT
#     )


# def agent_b_node(state: ChatState, llm):
#     return _run_agent(
#         state, llm, "Agent B", AGENT_B_PROMPT
#     )