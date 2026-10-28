import json
import re

from typing import Any

from assessment.pdi import (
    PDI_ITEMS,
    PDI_INSTRUMENT,
    PDI_VERSION,
    calculate_score,
)
from llm.provider import get_llm


def _parse_pdi_response(text: str) -> dict:
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON in PDI response.") from exc

    expected = {
        "endorsed", "distress", "preoccupation", "conviction"
    }

    if not isinstance(data, dict) or set(data) != expected:
        raise ValueError("PDI response has an invalid structure.")

    if type(data["endorsed"]) is not bool:
        raise ValueError("'endorsed' must be true or false.")

    for key in ("distress", "preoccupation", "conviction"):
        value = data[key]

        if not data["endorsed"]:
            if type(value) is not int or value != 0:
                raise ValueError(f"{key} must be 0 when not endorsed.")
        elif type(value) is not int or value not in range(1, 6):
            raise ValueError(f"{key} must be an integer from 1 to 5.")

    return data


def _ask_pdi_item(
    llm,
    item_number: int,
    topic: str,
    persona: dict,
    simulated_state: dict,
    previous_responses: list[dict],
) -> dict:
    prompt = f"""
Generate one synthetic response for a fictional persona.
This is a software research prototype, not a clinical evaluation.

These are paraphrased topics, not the original validated questionnaire items.
Do not diagnose the persona or assume that a cultural or religious belief
is pathological simply because it is present.

PERSONA:
{json.dumps(persona, ensure_ascii=False, default=str)}

CURRENT SIMULATED STATE:
{json.dumps(simulated_state, ensure_ascii=False, default=str)}

PREVIOUS RESPONSES IN THIS ASSESSMENT:
{json.dumps(previous_responses, ensure_ascii=False, default=str)}

CURRENT ITEM {item_number} OF {len(PDI_ITEMS)}:
{topic}

Return one JSON object with exactly these fields:
{{
  "endorsed": true or false,
  "distress": integer 1-5 or 0,
  "preoccupation": integer 1-5 or 0,
  "conviction": integer 1-5 or 0
}}

Rules:
- If endorsed is false, all three ratings must be 0.
- If endorsed is true, all three ratings must be integers from 1 to 5.
- Consider the persona and previous answers for reasonable consistency.
- Do not automatically copy previous answers.
- Do not force a particular total or a desired change in scores.
- Return JSON only, with no Markdown or explanation.
"""

    for attempt in range(2):
        response = llm.invoke(prompt)

        try:
            return _parse_pdi_response(str(response.content))
        except ValueError:
            if attempt == 1:
                raise

            prompt += (
                "\nYour previous output was invalid. "
                "Return only a valid JSON object with the exact schema."
            )

    raise RuntimeError("Could not generate a valid PDI response.")


def _run_pdi_assessment(state: dict, phase: str) -> dict:
    persona = state["persona"]
    simulated_state = state.get("simulated_state", {})
    llm = get_llm()

    # Local assessment memory; no additional PDI state fields required.
    responses: list[dict[str, Any]] = []

    for index, topic in enumerate(PDI_ITEMS, start=1):
        response = _ask_pdi_item(
            llm=llm,
            item_number=index,
            topic=topic,
            persona=persona,
            simulated_state=simulated_state,
            previous_responses=responses,
        )
        responses.append(response)

    scores = calculate_score(responses)

    record = {
        "instrument": PDI_INSTRUMENT,
        "instrument_version": PDI_VERSION,
        "phase": phase,
        "data_type": "synthetic",
        "standardized_administration": False,
        "responses": responses,
        "scores": scores,
    }

    # Preserve PHQ-9 and any other assessment records.
    all_records = dict(state.get("assessment_records", {}))
    phase_records = dict(all_records.get(phase, {}))
    phase_records["pdi"] = record
    all_records[phase] = phase_records

    return {"assessment_records": all_records}


def run_baseline_pdi_assessment(state: dict) -> dict:
    return _run_pdi_assessment(state, "baseline")


def run_followup_pdi_assessment(state: dict) -> dict:
    return _run_pdi_assessment(state, "followup")