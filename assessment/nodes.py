import re

from assessment.phq9 import PHQ9_QUESTIONS
from llm.provider import get_llm


FREQUENCY_GUIDE = """
Choose one response:
0 = Not at all
1 = Several days
2 = More than half the days
3 = Nearly every day
"""


def _parse_response(text: str) -> int:
    """Accept only a single valid score from 0 to 3."""
    match = re.fullmatch(r"\s*([0-3])\s*[.!]?\s*", text)

    if not match:
        raise ValueError(
            "The assessment model must return exactly one score: 0, 1, 2, or 3."
        )

    return int(match.group(1))


def _ask_one_question(llm, question: str, persona: dict, simulated_state: dict) -> int:
    prompt = f"""
You are simulating a fictional persona for a software experiment.
This is a synthetic assessment, not a real clinical evaluation.

Persona profile:
{persona}

Current simulated state:
{simulated_state}

Assessment item:
Over the last two weeks, how often has the persona experienced:
"{question}"

{FREQUENCY_GUIDE}

Answer with exactly one digit: 0, 1, 2, or 3.
Base the answer on the persona profile and simulated state.
Do not try to increase or decrease the score deliberately.
Do not include explanations or any other text.
"""

    # Retry once if the model returns malformed output.
    for attempt in range(2):
        response = llm.invoke(prompt)
        content = str(response.content).strip()

        try:
            return _parse_response(content)
        except ValueError:
            if attempt == 1:
                raise

            prompt += (
                "\nYour previous answer was invalid. "
                "Return exactly one digit: 0, 1, 2, or 3."
            )

    raise RuntimeError("Unable to obtain a valid assessment response.")


def _run_assessment(state: dict, phase: str) -> dict:
    persona = state["persona"]
    simulated_state = state.get("simulated_state", {})

    llm = get_llm()
    responses = []

    for question in PHQ9_QUESTIONS:
        score = _ask_one_question(
            llm=llm,
            question=question,
            persona=persona,
            simulated_state=simulated_state,
        )
        responses.append(score)

    result = {
        "current_assessment_responses": responses,
        "current_question_index": len(PHQ9_QUESTIONS),
        "assessment_phase": phase,
    }

    if phase == "baseline":
        result["baseline_responses"] = responses
        result["baseline_item9_flag"] = responses[8] > 0
    else:
        result["followup_responses"] = responses
        result["followup_item9_flag"] = responses[8] > 0

    return result


def run_baseline_assessment(state: dict) -> dict:
    return _run_assessment(state, "baseline")


def run_followup_assessment(state: dict) -> dict:
    return _run_assessment(state, "followup")
