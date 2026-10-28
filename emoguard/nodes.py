import json
from typing import Any

from langchain_core.messages import BaseMessage
from llm.provider import get_llm
import re


def _to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value)


def _latest_user_turn(messages: list) -> str:
    for message in reversed(messages):
        if getattr(message, "name", None) == "User Agent":
            return _to_text(message.content)
    return "(No User Agent message found.)"


def _transcript(messages: list) -> str:
    lines = []
    for message in messages:
        speaker = (
            getattr(message, "name", None)
            or getattr(message, "type", "unknown")
        )
        lines.append(f"{speaker}: {_to_text(message.content)}")
    return "\n".join(lines) or "(No conversation yet.)"



def _invoke_json(prompt: str) -> dict[str, Any]:
    """Extract JSON from model output and repair a common formatting error."""
    response = get_llm().invoke(prompt)
    raw = _to_text(response.content).strip()

    # Remove Markdown fences if present.
    raw = re.sub(
        r"```(?:json)?\s*",
        "",
        raw,
        flags=re.IGNORECASE,
    )
    raw = re.sub(r"\s*```", "", raw).strip()

    # Find the first complete JSON object, ignoring braces inside strings.
    start = raw.find("{")
    if start == -1:
        raise ValueError(
            f"No JSON object found in EmoGuard output:\n{raw}"
        )

    depth = 0
    in_string = False
    escaped = False
    end = None

    for i in range(start, len(raw)):
        char = raw[i]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end is None:
        raise ValueError(
            f"Incomplete JSON object in EmoGuard output:\n{raw}"
        )

    candidate = raw[start:end]

    # Repair patterns such as:
    # "Anxiety" (high confidence)
    # into:
    # "Anxiety (high confidence)"
    candidate = re.sub(
        r'"([^"\n]*)"\s*\(([^()\n]*)\)',
        lambda match: json.dumps(
            f"{match.group(1)} ({match.group(2)})",
            ensure_ascii=False,
        ),
        candidate,
    )

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "EmoGuard output contains malformed JSON after repair.\n"
            f"Parser error: {exc}\n"
            f"Extracted JSON:\n{candidate}\n"
            f"Full model output:\n{raw}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("EmoGuard output must be a JSON object.")

    return data


def capture_emoguard_before(state: dict) -> dict:
    """Capture a clean per-turn snapshot before the character responds."""
    return {
        "emoguard_state_before": dict(
            state.get("simulated_state", {})
        ),
        "emoguard_analysis": {},
        "emoguard_guidance": {},
    }

def emotion_watcher_node(state: dict) -> dict:
    """Identify possible emotional signals without diagnosing."""
    prompt = f"""
You are the Emotion Watcher in a research prototype.

Analyze the latest simulated person's conversational turn in context.
Identify observable emotional signals and possible distress, frustration,
uncertainty, or difficulty. Distinguish textual evidence from inference.
Do not diagnose, overstate certainty, or infer emotion from identity,
culture, religion, or a belief alone.

SIMULATED STATE:
{json.dumps(state.get("simulated_state", {}), ensure_ascii=False)}

LATEST USER TURN:
{_latest_user_turn(state.get("messages", []))}

CONVERSATION:
{_transcript(state.get("messages", []))}

Return only a JSON object with:
{{
  "observed_signals": ["specific textual signals"],
  "possible_emotions": [
    {{
        "emotion": "Anxiety",
        "confidence": "high"
    }}
],
  "possible_needs": ["what support may be useful"],
  "evidence": ["brief evidence from the conversation"],
  "uncertainties": ["what cannot be concluded"]
}}
These are hypotheses about a fictional simulation, not clinical findings.

STRICT JSON RULES:
- Return exactly one valid JSON object.
- Do not include introductory text, explanations, or Markdown fences.
- Every key and string value must use double quotes.
- Never append comments or parenthetical text outside a quoted value.
- Use the requested schema exactly.
"""
    result = _invoke_json(prompt)
    analysis = dict(state.get("emoguard_analysis", {}))
    analysis["emotion_watcher"] = result
    return {"emoguard_analysis": analysis}


def thought_refiner_node(state: dict) -> dict:
    """Surface interpretations or assumptions worth exploring."""
    watcher = state.get("emoguard_analysis", {}).get(
        "emotion_watcher", {}
    )

    prompt = f"""
You are the Thought Refiner in a research prototype.

Review the latest turn for possible interpretations, assumptions,
contradictions, or thinking patterns that could be explored collaboratively.
Do not label a thought as irrational merely because it is emotional or
unfamiliar. Do not diagnose. Consider context and alternative explanations.
Frame each point tentatively, as something to explore rather than a verdict.

LATEST USER TURN:
{_latest_user_turn(state.get("messages", []))}

EMOTION WATCHER NOTES:
{json.dumps(watcher, ensure_ascii=False)}

SIMULATED STATE:
{json.dumps(state.get("simulated_state", {}), ensure_ascii=False)}

Return only a JSON object with:
{{
  "possible_patterns": [
    {{
      "pattern": "tentative description",
      "evidence": "textual evidence",
      "alternative_interpretation": "another plausible reading",
      "gentle_question": "a nonjudgmental question to explore it"
    }}
  ],
  "what_not_to_assume": ["important uncertainties"]
}}
If no pattern is clearly supported, return an empty possible_patterns list.

STRICT JSON RULES:
- Return exactly one valid JSON object.
- Do not include introductory text, explanations, or Markdown fences.
- Every key and string value must use double quotes.
- Never append comments or parenthetical text outside a quoted value.
- Use the requested schema exactly.
"""
    result = _invoke_json(prompt)
    analysis = dict(state.get("emoguard_analysis", {}))
    analysis["thought_refiner"] = result
    return {"emoguard_analysis": analysis}


def dialog_guide_node(state: dict) -> dict:
    """Turn the analyses into practical, character-compatible suggestions."""
    analysis = state.get("emoguard_analysis", {})

    prompt = f"""
You are the Dialog Guide in a research prototype.

Suggest how the fictional character can respond supportively to the latest
turn. Be specific and actionable. Respect the character's supplied profile
and selected dialogue style. Avoid manipulation, shaming, unsupported
psychological claims, or forcing the simulated person to accept an
interpretation. Do not invent facts.

CHARACTER PROFILE:
{json.dumps(state.get("character_profile", {}), ensure_ascii=False)}

DIALOGUE STYLE:
{state.get("dialogue_style", "meow")}

LATEST USER TURN:
{_latest_user_turn(state.get("messages", []))}

EMOTION WATCHER:
{json.dumps(analysis.get("emotion_watcher", {}), ensure_ascii=False)}

THOUGHT REFINER:
{json.dumps(analysis.get("thought_refiner", {}), ensure_ascii=False)}

Return only a JSON object with:
{{
  "acknowledge": "what the character could acknowledge",
  "response_strategy": "suggested conversational approach",
  "optional_question": "a gentle question, or empty string",
  "avoid": ["responses or assumptions to avoid"],
  "priority": "one concise priority for this reply"
}}

STRICT JSON RULES:
- Return exactly one valid JSON object.
- Do not include introductory text, explanations, or Markdown fences.
- Every key and string value must use double quotes.
- Never append comments or parenthetical text outside a quoted value.
- Use the requested schema exactly.
"""
    result = _invoke_json(prompt)
    analysis = dict(state.get("emoguard_analysis", {}))
    analysis["dialog_guide"] = result
    return {"emoguard_analysis": analysis}


def emoguard_manager_node(state: dict) -> dict:
    """Combine module outputs into concise guidance for the character."""
    analysis = state.get("emoguard_analysis", {})

    prompt = f"""
You are the EmoGuard Manager. Consolidate the module outputs into concise
guidance for one character reply. Resolve conflicting suggestions by
prioritizing direct evidence, emotional sensitivity, uncertainty, and
natural conversation. Preserve the character's identity and style.
Give advice, not a script the character must copy verbatim.

CHARACTER PROFILE:
{json.dumps(state.get("character_profile", {}), ensure_ascii=False)}

SELECTED STYLE:
{state.get("dialogue_style", "meow")}

MODULE OUTPUTS:
{json.dumps(analysis, ensure_ascii=False)}

Return only a JSON object with:
{{
  "main_goal": "the most useful goal for this reply",
  "guidance": ["up to three concrete suggestions"],
  "optional_question": "a suitable question, or empty string",
  "avoid": ["important pitfalls"],
  "uncertainty_note": "what remains uncertain"
}}

STRICT JSON RULES:
- Return exactly one valid JSON object.
- Do not include introductory text, explanations, or Markdown fences.
- Every key and string value must use double quotes.
- Never append comments or parenthetical text outside a quoted value.
- Use the requested schema exactly.
"""
    guidance = _invoke_json(prompt)
    return {"emoguard_guidance": guidance}


def log_emoguard_after(state: dict) -> dict:
    """Record a comparable before/after snapshot for this completed turn."""
    messages = state.get("messages", [])
    character_reply = ""

    for message in reversed(messages):
        if getattr(message, "name", None) == "Character Agent":
            character_reply = _to_text(message.content)
            break

    record = {
        "round": state.get("round_count", 0) + 1,
        "emoguard_enabled": bool(state.get("emoguard_enabled", False)),
        "user_turn": _latest_user_turn(messages),
        "character_reply": character_reply,
        "state_before": dict(
            state.get("emoguard_state_before", {})
        ),
        "state_after": dict(state.get("simulated_state", {})),
        "module_outputs": dict(
            state.get("emoguard_analysis", {})
        ),
        "character_guidance": dict(
            state.get("emoguard_guidance", {})
        ),
    }

    history = list(state.get("emoguard_log", []))
    history.append(record)

    return {"emoguard_log": history}