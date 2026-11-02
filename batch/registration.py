"""Register batch experiment pairs and runs in SQLite."""

from typing import Any

from storage.database import get_session
from storage.repository import (
    calculate_hash,
    get_baseline,
    create_config,
    create_pair,
    create_pair_runs,
)

from batch.config import BatchConfig
from batch.matrix import (
    generate_experiment_matrix,
    validate_matrix,
)


def build_config_record(config: BatchConfig) -> dict[str, Any]:
    """Build a database-compatible config record."""

    full_config = config.to_dict()

    # Hash the complete configuration, including batch-only fields.
    config_hash = calculate_hash(full_config)

    # Pass only fields supported by ExperimentConfigCreate.
    return {
        "config_id": config.config_id,
        "experiment_name": config.experiment_name,
        "version": config.version,
        "model_name": config.model_name,
        "model_parameters": config.model_parameters or {},
        "max_rounds": config.max_rounds,
        "replicates": config.replicates,
        "dialogue_styles": list(config.dialogue_styles),
        "assessments": list(config.assessments),
        "emoguard_interval": config.emoguard_interval,
        "config_hash": config_hash,
        "config_json": full_config,
    }


def register_experiment(
    config: BatchConfig,
    personas: list[dict],
) -> dict[str, Any]:
    """
    Register all experiment pairs and their OFF/ON runs.

    Baselines must already exist in the database.

    Returns a summary of the registration.
    """

    if len(personas) != config.persona_count:
        raise ValueError(
            f"Expected {config.persona_count} personas, "
            f"received {len(personas)}."
        )

    # Generate and validate the complete experiment matrix.
    matrix = generate_experiment_matrix(config, personas)
    validate_matrix(matrix, config)

    session = get_session()

    registered_pairs = 0
    registered_runs = 0
    reused_pairs = 0
    reused_runs = 0

    try:
        # Create or reuse the immutable configuration.
        config_data = build_config_record(config)

        db_config = create_config(
            session=session,
            config_data=config_data,
        )

        session.commit()

        print(f"Configuration registered: {config.config_id}")
        print(f"Experiment pairs to register: {len(matrix)}")

        for index, matrix_pair in enumerate(matrix):

            persona_id = matrix_pair["persona_id"]
            replicate = matrix_pair["replicate"]

            # Every pair must use the baseline belonging to
            # this exact persona, replicate, and version.
            baseline = get_baseline(
                session=session,
                persona_id=persona_id,
                replicate=replicate,
                baseline_version=config.version,
            )

            if baseline is None:
                raise ValueError(
                    f"Missing baseline for persona={persona_id}, "
                    f"replicate={replicate}, "
                    f"version={config.version}. "
                    "Generate baselines before registration."
                )

            # Create or reuse the matched experiment pair.
            pair = create_pair(
                session=session,
                config_id=config.config_id,
                baseline_id=baseline.baseline_id,
                persona_id=persona_id,
                character_id=matrix_pair["character_id"],
                dialogue_style=matrix_pair["dialogue_style"],
                replicate=replicate,
            )

            # Alternate condition order to reduce systematic
            # order effects across the benchmark.
            first_condition = (
                "off" if index % 2 == 0 else "on"
            )

            runs = create_pair_runs(
                session=session,
                pair_id=pair.pair_id,
                model_name=config.model_name,
                first_condition=first_condition,
            )

            # Verify that both conditions exist exactly once.
            conditions = [run.condition for run in runs]

            if len(conditions) != 2 or set(conditions) != {
                "off",
                "on",
            }:
                raise ValueError(
                    f"Invalid run structure for pair {pair.pair_id}."
                )

            registered_pairs += 1
            registered_runs += len(runs)

            if pair.created_at is not None:
                # Counts here represent pairs returned by the
                # repository, including previously registered ones.
                pass

            session.commit()

            if (index + 1) % 10 == 0 or index + 1 == len(matrix):
                print(
                    f"Registration progress: "
                    f"{index + 1}/{len(matrix)} pairs"
                )

        expected_pairs = (
            config.persona_count
            * len(config.character_ids)
            * len(config.dialogue_styles)
            * config.replicates
        )

        expected_runs = expected_pairs * len(config.conditions)

        if registered_pairs != expected_pairs:
            raise ValueError(
                f"Expected {expected_pairs} registered pairs, "
                f"got {registered_pairs}."
            )

        if registered_runs != expected_runs:
            raise ValueError(
                f"Expected {expected_runs} registered runs, "
                f"got {registered_runs}."
            )

        return {
            "config_id": config.config_id,
            "pairs": registered_pairs,
            "runs": registered_runs,
            "expected_pairs": expected_pairs,
            "expected_runs": expected_runs,
        }

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()