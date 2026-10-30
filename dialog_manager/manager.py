import json
import re
from typing import Any

from llm.provider import get_llm


VALID_MODES = {"normal", "topic_shift", "clarify", "uncertain"}


def _message_text(message: Any) -> str:
    """Extract readable text from a LangChain message."""
    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content.strip()

    return str(content).strip()


def _format_transcript(messages: list, limit: int = 12) -> str:
    """Format recent conversation messages for the manager."""
    if not messages:
        return "(The conversation has not started yet.)"

    lines = []

    for message in messages[-limit:]:
        speaker = getattr(message, "name", None)

        if not speaker:
            speaker = getattr(message, "type", "unknown")

        lines.append(f"{speaker}: {_message_text(message)}")

    return "\n".join(lines)


def _parse_manager_output(raw: str) -> dict:
    """Parse and validate the manager's JSON response."""
    raw = raw.strip()

    # Allow JSON enclosed in a Markdown code fence.
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Dialog Manager returned invalid JSON."
        ) from exc

    required = {
        "mode",
        "loop_detected",
        "current_topic",
        "reason",
        "next_topic",
        "instructions",
    }

    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError(
            "Dialog Manager output is missing required fields."
        )

    if data["mode"] not in VALID_MODES:
        raise ValueError("Dialog Manager returned an invalid mode.")

    if type(data["loop_detected"]) is not bool:
        raise ValueError("loop_detected must be a boolean.")

    for field in (
        "current_topic",
        "reason",
        "next_topic",
        "instructions",
    ):
        if not isinstance(data[field], str):
            raise ValueError(f"{field} must be a string.")

    # Prevent empty instructions from reaching the agents.
    if not data["instructions"].strip():
        raise ValueError("Dialog Manager instructions cannot be empty.")

    return {
        "mode": data["mode"],
        "loop_detected": data["loop_detected"],
        "current_topic": data["current_topic"][:300],
        "reason": data["reason"][:1000],
        "next_topic": data["next_topic"][:300],
        "instructions": data["instructions"][:1500],
    }


def dialog_manager_node(state: dict) -> dict:
    """
    Analyze conversational progress and plan the next exchange.

    This node uses an LLM for semantic reasoning. Round limits and
    graph routing remain controlled by Python and LangGraph.
    """
    round_count = state.get("round_count", 0)
    max_rounds = state.get("max_rounds", 8)

    if not 1 <= max_rounds <= 10:
        raise ValueError("max_rounds must be between 1 and 10.")

    if round_count >= max_rounds:
        raise ValueError(
            "Dialog Manager was called after the maximum round count."
        )

    transcript = _format_transcript(
        state.get("messages", [])
    )

    dialogue_style = state.get("dialogue_style", "meow")
    previous_guidance = state.get("dialogue_guidance", {})

    prompt = f"""
You are the Dialog Manager for EmoAgent Lite, a multi-agent
conversation research prototype.

Your job is to plan the next conversational exchange, not to
write the User Agent's or Character Agent's actual dialogue.

CURRENT EXPERIMENT:
- Completed rounds: {round_count}
- Maximum rounds: {max_rounds}
- Character dialogue style: {dialogue_style}

PREVIOUS MANAGER GUIDANCE:
{json.dumps(previous_guidance, ensure_ascii=False, default=str)}

RECENT CONVERSATION:
{transcript}

Analyze the conversation semantically.

1. Identify the main topic currently being discussed.
2. Determine whether the conversation is progressing or circling
   around the same idea using different wording.
3. A loop can be semantic: for example, repeated expressions of
   failure or frustration may indicate repetition even when the
   exact words differ.
4. Do not label a conversation as a loop merely because a topic
   is revisited. Consider whether new information or perspective
   is being introduced.
5. If the conversation is stuck, recommend a relevant topic shift
   or a clarifying question.
6. Otherwise, recommend a natural continuation.
7. Respect the selected character dialogue style, but do not
   prioritize style over respectful and safe behavior.
8. Do not deliberately exploit a simulated persona's vulnerabilities.
9. Do not diagnose the persona or infer clinical facts.
10. Never change the experiment's round limit.

Return ONLY a valid JSON object with exactly these fields:
{{
  "mode": "normal",
  "loop_detected": false,
  "current_topic": "brief topic description",
  "reason": "brief explanation of your decision",
  "next_topic": "suggested next topic or continuation",
  "instructions": "actionable guidance for the next exchange"
}}

Allowed mode values:
- normal: continue the conversation naturally
- topic_shift: move away from an unproductive repeated topic
- clarify: ask a relevant clarifying question
- uncertain: insufficient context to confidently decide

Set loop_detected to true only when there is evidence of
unproductive semantic repetition.

Do not include Markdown fences or additional text.
"""

    llm = get_llm()
    last_error = None

    # Retry once if the model returns malformed output.
    for attempt in range(2):
        current_prompt = prompt

        if attempt == 1:
            current_prompt += """
Your previous response was invalid.
Return a valid JSON object with all six required fields,
valid mode values, and the correct field types.
"""

        response = llm.invoke(current_prompt)

        try:
            guidance = _parse_manager_output(
                str(response.content)
            )
            break
        except ValueError as exc:
            last_error = exc
    else:
        # Fail safely instead of inventing a manager decision.
        guidance = {
            "mode": "uncertain",
            "loop_detected": False,
            "current_topic": "current conversation",
            "reason": (
                f"Manager output validation failed: {last_error}"
            ),
            "next_topic": "continue the current topic",
            "instructions": (
                "Continue naturally, avoid repetition, and do not "
                "introduce an unverified topic shift."
            ),
        }

    manager_log = {
        "completed_rounds": round_count,
        "next_round": round_count + 1,
        "max_rounds": max_rounds,
        "dialogue_style": dialogue_style,
        **guidance,
    }

    return {
        "dialogue_guidance": guidance,
        "dialog_manager_log": manager_log,
    }
