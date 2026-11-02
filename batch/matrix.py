'''This generates all matched experiment pairs and their two conditions.'''
from itertools import product
from uuid import uuid4

from batch.config import BatchConfig


def generate_experiment_matrix(
    config: BatchConfig,
    personas: list[dict],
) -> list[dict]:

    if len(personas) != config.persona_count:
        raise ValueError(
            f"Expected {config.persona_count} personas, "
            f"received {len(personas)}."
        )

    matrix = []

    dimensions = product(
        personas,
        config.character_ids,
        config.dialogue_styles,
        range(1, config.replicates + 1),
    )

    for persona, character_id, dialogue_style, replicate in dimensions:

        persona_id = persona["id"]

        pair = {
            "pair_id": str(uuid4()),
            "persona_id": persona_id,
            "character_id": character_id,
            "dialogue_style": dialogue_style,
            "replicate": replicate,
            "runs": [
                {"condition": condition}
                for condition in config.conditions
            ],
        }

        matrix.append(pair)

    return matrix


def validate_matrix(
    matrix: list[dict],
    config: BatchConfig,
) -> None:
    """Validate experiment matrix dimensions and uniqueness."""

    expected_pairs = (
        config.persona_count
        * len(config.character_ids)
        * len(config.dialogue_styles)
        * config.replicates
    )

    expected_runs = expected_pairs * len(config.conditions)

    if len(matrix) != expected_pairs:
        raise ValueError(
            f"Expected {expected_pairs} pairs, got {len(matrix)}."
        )

    all_pair_ids = set()
    all_dimensions = set()
    total_runs = 0

    for pair in matrix:
        if pair["pair_id"] in all_pair_ids:
            raise ValueError("Duplicate pair ID detected.")

        all_pair_ids.add(pair["pair_id"])

        dimensions = (
            pair["persona_id"],
            pair["character_id"],
            pair["dialogue_style"],
            pair["replicate"],
        )

        if dimensions in all_dimensions:
            raise ValueError(
                f"Duplicate experiment combination: {dimensions}"
            )

        all_dimensions.add(dimensions)

        conditions = [
            run["condition"]
            for run in pair["runs"]
        ]

        if set(conditions) != set(config.conditions):
            raise ValueError(
                f"Invalid conditions for pair {pair['pair_id']}."
            )

        if len(conditions) != len(config.conditions):
            raise ValueError(
                f"Incorrect run count for pair {pair['pair_id']}."
            )

        total_runs += len(pair["runs"])

    if total_runs != expected_runs:
        raise ValueError(
            f"Expected {expected_runs} runs, got {total_runs}."
        )