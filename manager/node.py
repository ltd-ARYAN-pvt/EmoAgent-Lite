from assessment.scoring import (
    calculate_phq9_score,
    compare_scores,
)

from assessment.pdi import (
    PDI_INSTRUMENT,
    calculate_score as calculate_pdi_score,
)

def _get_phq9_record(state: dict, phase: str) -> dict:
    records = state.get("assessment_records", {})
    phase_records = records.get(phase, {})
    record = phase_records.get("phq9")

    if not isinstance(record, dict):
        raise ValueError(
            f"Missing PHQ-9 {phase} assessment record."
        )

    if record.get("phase") != phase:
        raise ValueError(
            f"PHQ-9 record phase does not match '{phase}'."
        )

    if record.get("data_type") != "synthetic":
        raise ValueError(
            "Expected a synthetic PHQ-9 assessment record."
        )

    scores = record.get("scores")
    if not isinstance(scores, dict):
        raise ValueError("PHQ-9 record is missing scores.")

    score = scores.get("total")
    if type(score) is not int or not 0 <= score <= 27:
        raise ValueError("PHQ-9 total score must be an integer from 0 to 27.")

    return record


def _get_pdi_record(state: dict, phase: str) -> dict:
    """Validate a PDI topic-prototype record and its calculated scores."""

    records = state.get("assessment_records", {})
    phase_records = records.get(phase, {})
    record = phase_records.get("pdi")

    if not isinstance(record, dict):
        raise ValueError(f"Missing PDI {phase} assessment record.")

    if record.get("phase") != phase:
        raise ValueError(f"PDI record has an incorrect phase: {phase}.")

    if record.get("instrument") != PDI_INSTRUMENT:
        raise ValueError("Unexpected PDI instrument identifier.")

    if record.get("data_type") != "synthetic":
        raise ValueError("PDI record must contain synthetic data.")

    if record.get("standardized_administration") is not False:
        raise ValueError(
            "PDI topic-prototype results must be marked as non-standardized."
        )

    responses = record.get("responses")
    calculated_scores = calculate_pdi_score(responses)
    stored_scores = record.get("scores")

    if not isinstance(stored_scores, dict):
        raise ValueError("PDI record is missing its scores.")

    if stored_scores != calculated_scores:
        raise ValueError("Stored PDI scores do not match the responses.")

    return record



def manager_initialize(state: dict) -> dict:
    _get_phq9_record(state, "baseline")

    enabled = state.get("enabled_assessments", ["phq9"])

    if not isinstance(enabled, list):
        raise ValueError("'enabled_assessments' must be a list.")

    if "phq9" not in enabled:
        raise ValueError("PHQ-9 must remain enabled for this experiment.")

    if any(item not in {"phq9", "pdi"} for item in enabled):
        raise ValueError("Unsupported assessment in enabled_assessments.")

    if "pdi" in enabled:
        _get_pdi_record(state, "baseline")

    max_rounds = state.get("max_rounds", 8)

    if type(max_rounds) is not int or not 1 <= max_rounds <= 10:
        raise ValueError("max_rounds must be an integer between 1 and 10.")

    return {"round_count": 0}



def manager_after_turn(state):
    # Called after the Character Agent has replied.
    return {
        "round_count": state["round_count"] + 1,
    }


def route_after_turn(state):
    if state["round_count"] < state["max_rounds"]:
        return "continue"
    return "finish"



def manager_finalize(state: dict) -> dict:
    baseline_phq9 = _get_phq9_record(state, "baseline")
    followup_phq9 = _get_phq9_record(state, "followup")

    baseline_score = baseline_phq9["scores"]["total"]
    followup_score = followup_phq9["scores"]["total"]

    comparison = compare_scores(baseline_score, followup_score)

    result = {
        "experiment_id": state["experiment_id"],
        "persona_id": state["persona"]["id"],
        "character_id": state["character_profile"]["id"],
        "dialogue_style": state.get("dialogue_style", "meow"),
        "rounds_completed": state["round_count"],
        **comparison,
        "assessment_records": state["assessment_records"],
    }

    enabled = state.get("enabled_assessments", ["phq9"])

    if "pdi" in enabled:
        baseline_pdi = _get_pdi_record(state, "baseline")
        followup_pdi = _get_pdi_record(state, "followup")

        baseline_pdi_scores = baseline_pdi["scores"]
        followup_pdi_scores = followup_pdi["scores"]

        score_keys = (
            "endorsement_count",
            "distress_sum",
            "preoccupation_sum",
            "conviction_sum",
            "grand_total",
        )

        result["pdi_comparison"] = {
            key: {
                "baseline": baseline_pdi_scores[key],
                "followup": followup_pdi_scores[key],
                "delta": (
                    followup_pdi_scores[key] - baseline_pdi_scores[key]
                ),
            }
            for key in score_keys
        }

    return {"experiment_result": result}