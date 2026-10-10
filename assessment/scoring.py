def calculate_phq9_score(responses: list[int]) -> int:
    if len(responses) != 9:
        raise ValueError("PHQ-9 requires exactly 9 responses.")

    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or value not in (0, 1, 2, 3)
        for value in responses
    ):
        raise ValueError("Each response must be an integer from 0 to 3.")

    return sum(responses)


def compare_scores(baseline: int, followup: int) -> dict:
    delta = followup - baseline

    if delta > 0:
        direction = "increased"
    elif delta < 0:
        direction = "decreased"
    else:
        direction = "unchanged"

    return {
        "baseline_score": baseline,
        "followup_score": followup,
        "delta": delta,
        "direction": direction,
        "data_type": "synthetic",
    }