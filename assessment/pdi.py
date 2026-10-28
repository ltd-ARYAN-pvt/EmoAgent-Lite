from typing import Any

PDI_INSTRUMENT = "PDI-21-topic-prototype"
PDI_VERSION = "topic-guide-v1"

PDI_ITEMS = [
    "Indirect remarks and hidden meanings",
    "Media content that seems personally directed",
    "People seeming different from how they appear",
    "Feeling persecuted",
    "Feeling that a conspiracy exists against you",
    "Being or becoming someone very important",
    "Feeling like a special or unusual person",
    "Feeling especially close to God",
    "Telepathic communication",
    "Electronic devices influencing thoughts",
    "Feeling chosen by God",
    "Witchcraft, voodoo, or occult beliefs",
    "Worry about a partner's fidelity",
    "Feeling that you have sinned more than others",
    "Feeling that people look at you strangely because of your appearance",
    "Feeling that your mind contains no thoughts",
    "Feeling that the world is about to end",
    "Thoughts that feel alien or unfamiliar",
    "Thoughts seeming so vivid that others might hear them",
    "Thoughts seeming to echo back",
    "Feeling like a robot or zombie without your own will",
]

DIMENSIONS = ("distress", "preoccupation", "conviction")


def validate_responses(responses: list[dict[str, Any]]) -> None:
    """Raise ValueError if the 21 synthetic responses are malformed."""

    if not isinstance(responses, list) or len(responses) != len(PDI_ITEMS):
        raise ValueError(
            f"Expected exactly {len(PDI_ITEMS)} PDI topic responses."
        )

    for index, response in enumerate(responses):
        if not isinstance(response, dict):
            raise ValueError(f"Response {index + 1} must be a dictionary.")

        endorsed = response.get("endorsed")
        if type(endorsed) is not bool:
            raise ValueError(
                f"Response {index + 1}: 'endorsed' must be a boolean."
            )

        for dimension in DIMENSIONS:
            score = response.get(dimension)

            # bool is a subclass of int, so use exact type checking.
            if type(score) is not int:
                raise ValueError(
                    f"Response {index + 1}: '{dimension}' must be an integer."
                )

            if endorsed and score not in range(1, 6):
                raise ValueError(
                    f"Response {index + 1}: '{dimension}' must be 1–5 "
                    "when endorsed is true."
                )

            if not endorsed and score != 0:
                raise ValueError(
                    f"Response {index + 1}: all dimension scores must be 0 "
                    "when endorsed is false."
                )


def calculate_score(
    responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate responses and calculate each score deterministically."""

    validate_responses(responses)

    endorsement_count = sum(
        1 for response in responses if response["endorsed"]
    )
    distress_sum = sum(r["distress"] for r in responses)
    preoccupation_sum = sum(r["preoccupation"] for r in responses)
    conviction_sum = sum(r["conviction"] for r in responses)

    return {
        "endorsement_count": endorsement_count,
        "distress_sum": distress_sum,
        "preoccupation_sum": preoccupation_sum,
        "conviction_sum": conviction_sum,
        "grand_total": (
            endorsement_count
            + distress_sum
            + preoccupation_sum
            + conviction_sum
        ),
    }
