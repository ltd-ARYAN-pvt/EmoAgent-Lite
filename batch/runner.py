"""Execute registered OFF/ON experiment runs."""

import json
from copy import deepcopy
from pathlib import Path

from agent.graph import build_graph
from batch.baselines import create_initial_simulated_state
from batch.config import BatchConfig

from storage.database import get_session
from storage.repository import (
    get_baseline,
    get_incomplete_pairs,
    get_run,
    start_run,
    complete_run,
    fail_run,
    add_artifact,
    get_config,
    refresh_pair_status,
)
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from storage.models import ExperimentPair, ExperimentRun
from langchain_core.messages import messages_to_dict
from dotenv import load_dotenv
load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHARACTER_DIR = PROJECT_ROOT / "data" / "characters"


def load_character_profile(character_id: str) -> dict:
    """Load a character profile using the same location as run_agents.py."""

    character_path = CHARACTER_DIR / f"{character_id}.json"

    if not character_path.exists():
        raise FileNotFoundError(
            f"Character profile not found: {character_path}"
        )

    with character_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_run_artifacts(
    session,
    run_id: str,
    config_id: str,
    result_state: dict,
) -> None:
    """Save transcript, assessment records, and EmoGuard logs."""

    artifact_dir = (
        PROJECT_ROOT
        / "results"
        / "artifacts"
        / config_id
        / run_id
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)

    artifacts = {
        "transcript": messages_to_dict(
            result_state.get("messages", [])
        ),
        "assessment": result_state.get(
            "assessment_records", {}
        ),
        "emoguard_log": {
            "log": result_state.get("emoguard_log", []),
            "intervention_count": result_state.get(
                "emoguard_intervention_count", 0
            ),
            "intervention_rounds": result_state.get(
                "emoguard_intervention_rounds", []
            ),
        },
    }

    for artifact_type, content in artifacts.items():
        file_path = artifact_dir / f"{artifact_type}.json"

        with file_path.open("w", encoding="utf-8") as file:
            json.dump(
                content,
                file,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        add_artifact(
            session=session,
            run_id=run_id,
            artifact_type=artifact_type,
            file_path=str(file_path),
        )
        

def recover_stale_runs(
    config_id: str,
    stale_after_minutes: int = 60,
    dry_run: bool = True,
) -> list[str]:
    """
    Find runs that have been stuck in 'running' beyond the
    configured age threshold.

    dry_run=True:
        Report stale runs without modifying the database.

    dry_run=False:
        Mark stale runs as failed so start_run() can retry them.

    Only use this when no other batch runner is actively executing
    this experiment.
    """

    if stale_after_minutes < 0:
        raise ValueError("stale_after_minutes cannot be negative.")

    session = get_session()

    try:
        config = get_config(session, config_id)

        if config is None:
            raise ValueError(f"Unknown configuration: {config_id}")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cutoff = now - timedelta(minutes=stale_after_minutes)

        stale_runs = list(
            session.scalars(
                select(ExperimentRun)
                .join(ExperimentPair)
                .where(
                    ExperimentPair.config_db_id == config.id,
                    ExperimentRun.status == "running",
                    ExperimentRun.started_at.is_not(None),
                    ExperimentRun.started_at < cutoff,
                )
                .order_by(ExperimentRun.started_at)
            ).all()
        )

        recovered_ids = []

        if not stale_runs:
            print("No stale running experiments found.")
            return recovered_ids

        print(f"Found {len(stale_runs)} potentially stale runs.")

        for run in stale_runs:
            age_minutes = (
                now - run.started_at
            ).total_seconds() / 60

            print(
                f"Run: {run.run_id} | "
                f"Condition: {run.condition.upper()} | "
                f"Age: {age_minutes:.1f} minutes"
            )

            recovered_ids.append(run.run_id)

            if dry_run:
                continue

            run.status = "failed"
            run.error_message = (
                "Recovered after exceeding the stale-run threshold. "
                "Safe to retry after checking that no original process "
                "is still executing."
            )
            run.completed_at = now

            session.flush()

            refresh_pair_status(
                session=session,
                pair_id=run.pair.pair_id,
            )

        if dry_run:
            print(
                "\nDry run only: no database records were changed."
            )
        else:
            session.commit()
            print(
                f"\nRecovered {len(recovered_ids)} stale runs. "
                "They can now be retried."
            )

        return recovered_ids

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def build_batch_state(
    pair,
    persona: dict,
    baseline_record: dict,
    character_profile: dict,
    config: BatchConfig,
    condition: str,
) -> dict:
    """Create a fresh, isolated initial state for one run."""

    if condition not in {"off", "on"}:
        raise ValueError(f"Unsupported condition: {condition}")

    return {
        "experiment_id": f"{pair.pair_id}-{condition}",
        "persona": deepcopy(persona),
        "character_profile": deepcopy(character_profile),
        "dialogue_style": pair.dialogue_style,

        "messages": [],

        "simulated_state": create_initial_simulated_state(),

        # Inject the existing baseline; do not generate another one.
        "assessment_phase": "conversation",
        "assessment_records": {
            "baseline": {
                "phq9": deepcopy(baseline_record),
            }
        },
        "baseline_assessment_provided": True,
        "enabled_assessments": ["phq9"],
        "current_question_index": 0,
        "current_assessment_responses": [],

        "round_count": 0,
        "max_rounds": config.max_rounds,

        "dialog_manager_log_interval": 1,

        # Batch-specific EmoGuard configuration.
        "batch_mode": True,
        "emoguard_enabled": condition == "on",
        "emoguard_interval": config.emoguard_interval,
        "emoguard_ran_this_turn": False,
        "emoguard_intervention_count": 0,
        "emoguard_intervention_rounds": [],
        "emoguard_log": [],
    }


def execute_one_run(
    graph,
    session,
    pair,
    run,
    baseline_record: dict,
    persona: dict,
    character_profile: dict,
    config: BatchConfig,
) -> None:
    """Execute and persist one OFF or ON run."""

    if run.status == "completed":
        print(
            f"[SKIP] Pair {pair.pair_id} "
            f"{run.condition.upper()} already completed."
        )
        return

    condition = run.condition

    print(
        f"\n[START] {pair.persona_id} | "
        f"{pair.character_id} | "
        f"{pair.dialogue_style} | "
        f"Replicate {pair.replicate} | "
        f"{condition.upper()}"
    )

    try:
        # Mark the run as active before making any LLM calls.
        run = start_run(session, run.run_id)
        session.commit()

        # Use a fresh state for every condition.
        initial_state = build_batch_state(
            pair=pair,
            persona=persona,
            baseline_record=baseline_record,
            character_profile=character_profile,
            config=config,
            condition=condition,
        )

        # Inject the persona explicitly instead of relying on
        # mutable ORM objects inside the graph.
        initial_state["persona"] = deepcopy(persona)

        result_state = graph.invoke(initial_state)
        save_run_artifacts(
            session=session,
            run_id=run.run_id,
            config_id=config.config_id,
            result_state=result_state,
        )

        # Extract baseline and follow-up PHQ-9 records.
        records = result_state.get("assessment_records", {})

        followup_record = (
            records.get("followup", {}).get("phq9")
        )

        if not isinstance(followup_record, dict):
            raise ValueError(
                "Graph did not return a follow-up PHQ-9 record."
            )

        final_score = followup_record.get("scores", {}).get("total")

        if type(final_score) is not int or not 0 <= final_score <= 27:
            raise ValueError(
                f"Invalid follow-up PHQ-9 score: {final_score}"
            )

        initial_score = baseline_record["scores"]["total"]

        intervention_count = result_state.get(
            "emoguard_intervention_count",
            0,
        )

        intervention_rounds = result_state.get(
            "emoguard_intervention_rounds",
            [],
        )

        # Save the completed result.
        complete_run(
            session=session,
            run_id=run.run_id,
            result_data={
                "initial_score": initial_score,
                "final_score": final_score,
                "intervention_count": intervention_count,
                "intervention_rounds": intervention_rounds,
            },
        )

        session.commit()

        print(
            f"[COMPLETED] {condition.upper()} | "
            f"PHQ-9: {initial_score} -> {final_score} | "
            f"Interventions: {intervention_count}"
        )

    except Exception as error:
        session.rollback()

        # Reload the run after rollback before changing its status.
        current_run = get_run(
            session=session,
            pair_id=pair.pair_id,
            condition=condition,
        )

        if current_run is not None and current_run.status == "running":
            fail_run(
                session=session,
                run_id=current_run.run_id,
                error_message=str(error)[:2000],
            )
            session.commit()

        print(
            f"[FAILED] {condition.upper()} | {error}"
        )

        # Do not stop the entire benchmark because one run failed.
        return


def run_batch(
    config: BatchConfig,
    limit_pairs: int | None = None,
) -> None:
    """
    Execute all incomplete pairs for a registered configuration.

    limit_pairs is useful for small pilot tests.
    """

    graph = build_graph()
    session = get_session()

    try:
        pairs = get_incomplete_pairs(
            session=session,
            config_id=config.config_id,
        )

        # Deterministic ordering for the first implementation.
        pairs.sort(key=lambda pair: pair.created_at)

        if limit_pairs is not None:
            if limit_pairs < 1:
                raise ValueError("limit_pairs must be positive.")
            pairs = pairs[:limit_pairs]

        print(f"Pairs selected for execution: {len(pairs)}")

        for index, pair in enumerate(pairs, start=1):

            # Retrieve the exact baseline associated with this pair.
            baseline = get_baseline(
                session=session,
                persona_id=pair.persona_id,
                replicate=pair.replicate,
                baseline_version=config.version,
            )

            if baseline is None:
                raise ValueError(
                    f"Missing baseline for pair {pair.pair_id}."
                )

            baseline_record = baseline.assessment_json
            persona = baseline.persona.profile_json

            # Cache the persona on this in-memory pair object
            # so build_batch_state can use it.
            # pair._batch_persona = persona

            character_profile = load_character_profile(
                pair.character_id
            )

            # Always follow the stored execution order.
            runs = sorted(
                pair.runs,
                key=lambda item: item.execution_order,
            )

            print(
                f"\n========== Pair {index}/{len(pairs)} "
                f"({pair.pair_id}) =========="
            )

            for run in runs:
                # Refresh the run in case a previous operation changed it.
                current_run = get_run(
                    session=session,
                    pair_id=pair.pair_id,
                    condition=run.condition,
                )

                if current_run is None:
                    raise ValueError(
                        f"Missing {run.condition} run for "
                        f"pair {pair.pair_id}."
                    )

                execute_one_run(
                    graph=graph,
                    session=session,
                    pair=pair,
                    run=current_run,
                    baseline_record=baseline_record,
                    persona=persona,
                    character_profile=character_profile,
                    config=config,
                )

            session.expire_all()

        print("\nBatch execution pass finished.")

    finally:
        session.close()