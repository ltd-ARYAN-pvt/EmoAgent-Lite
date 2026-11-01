from typing import Any

from assessment.nodes import run_baseline_assessment

# Adjust these imports to match the package paths in your project.
from storage.database import get_session
from storage.repository import (
    get_baseline,
    create_baseline,
    validate_baseline_record,
    get_or_create_persona,
)


def create_initial_simulated_state() -> dict[str, Any]:
    """
    Return a fresh initial simulated state.

    Keep this consistent between baseline generation and
    the corresponding OFF/ON conversation runs.
    """
    return {
        "mood": "neutral",
        "distress_level": 5,
        "perceived_stress": 5,
        "recent_experiences": [],
        "current_interpretation": (
            "The conversation has not started yet."
        ),
    }


def generate_baseline(
    persona: dict,
) -> dict:
    """
    Generate one synthetic PHQ-9 baseline using the
    existing V4 assessment node.
    """

    initial_state = {
        "persona": persona,
        "simulated_state": create_initial_simulated_state(),
        "assessment_records": {},
        "current_assessment_responses": [],
        "current_question_index": 0,
        "assessment_phase": "baseline",
    }

    result = run_baseline_assessment(initial_state)

    records = result.get("assessment_records", {})
    baseline_record = records.get("baseline", {}).get("phq9")

    if not isinstance(baseline_record, dict):
        raise ValueError(
            f"Baseline generation failed for persona {persona['id']}."
        )

    validate_baseline_record(baseline_record)

    return baseline_record


def generate_or_reuse_baselines(
    personas: list[dict],
    replicates: int = 3,
    baseline_version: str = "4.2",
) -> dict[tuple[str, int], dict]:
    """
    Generate missing baselines and reuse existing ones.

    Returns:
        {
            ("1-1", 1): assessment_record,
            ("1-1", 2): assessment_record,
            ...
        }
    """

    if replicates < 1:
        raise ValueError("replicates must be positive.")

    baselines = {}

    session = get_session()

    try:
        for persona_index, persona in enumerate(personas, start=1):

            persona_id = persona["id"]

            # Detect changes to previously stored persona profiles.
            get_or_create_persona(session, persona)

            for replicate in range(1, replicates + 1):

                key = (persona_id, replicate)

                existing = get_baseline(
                    session=session,
                    persona_id=persona_id,
                    replicate=replicate,
                    baseline_version=baseline_version,
                )

                if existing is not None:

                    # Validate stored data before trusting it.
                    record = existing.assessment_json
                    validate_baseline_record(record)

                    if existing.total_score != record["scores"]["total"]:
                        raise ValueError(
                            f"Stored baseline score mismatch: {key}"
                        )

                    if existing.responses_json != record["responses"]:
                        raise ValueError(
                            f"Stored baseline responses mismatch: {key}"
                        )

                    baselines[key] = record

                    print(
                        f"[REUSED] {persona_id} "
                        f"Replicate {replicate}"
                    )

                    continue

                print(
                    f"[GENERATING] {persona_id} "
                    f"Replicate {replicate}"
                )

                record = generate_baseline(persona)

                baseline = create_baseline(
                    session=session,
                    persona=persona,
                    replicate=replicate,
                    assessment_record=record,
                    baseline_version=baseline_version,
                )

                # Commit each baseline separately.
                # If a later generation fails, previous baselines survive.
                session.commit()

                baselines[key] = baseline.assessment_json

                print(
                    f"[SAVED] {persona_id} "
                    f"Replicate {replicate} "
                    f"Score: {baseline.total_score}"
                )

            print(
                f"Progress: {persona_index}/{len(personas)} personas"
            )

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()

    return baselines