from assessment.scoring import (
    calculate_phq9_score,
    compare_scores,
)


def manager_initialize(state):
    baseline_score = calculate_phq9_score(
        state["baseline_responses"]
    )

    if state["max_rounds"] < 1:
        raise ValueError("max_rounds must be at least 1.")

    return {
        "baseline_score": baseline_score,
        "round_count": 0,
    }


def manager_after_turn(state):
    # Called after the Character Agent has replied.
    return {
        "round_count": state["round_count"] + 1,
    }


def route_after_turn(state):
    if state["round_count"] < state["max_rounds"]:
        return "continue"
    return "finish"


def manager_finalize(state):
    followup_score = calculate_phq9_score(
        state["followup_responses"]
    )

    comparison = compare_scores(
        state["baseline_score"],
        followup_score,
    )

    result = {
        "experiment_id": state["experiment_id"],
        "persona_id": state["persona"]["id"],
        "character_id": state["character_profile"]["id"],
        "dialogue_style": state.get("dialogue_style", "meow"),
        "rounds_completed": state["round_count"],
        **comparison,
    }

    return {
        "followup_score": followup_score,
        "score_delta": comparison["delta"],
        "experiment_result": result,
    }