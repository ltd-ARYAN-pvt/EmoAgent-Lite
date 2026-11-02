from dataclasses import replace
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from data.persona_loader import load_personas
from storage.database import initialize_database, get_session
from storage.models import ExperimentPair, ExperimentRun

from batch.config import BatchConfig
from batch.baselines import generate_or_reuse_baselines
from batch.registration import register_experiment
from batch.runner import recover_stale_runs, run_batch


CONFIG_ID = "emagent-v4.2-crash-recovery-test"


def get_run_record(pair_id, condition):
    session = get_session()

    try:
        return session.scalar(
            select(ExperimentRun)
            .join(ExperimentPair)
            .where(
                ExperimentPair.pair_id == pair_id,
                ExperimentRun.condition == condition,
            )
        )
    finally:
        session.close()


def main():
    initialize_database()

    # Use one existing test persona.
    personas = load_personas()[:1]

    config = replace(
        BatchConfig(),
        config_id=CONFIG_ID,
        experiment_name="EmoAgent V4.2 Crash Recovery Test",
        persona_count=1,
        character_ids=("alex",),
        dialogue_styles=("meow",),
        replicates=1,
        max_rounds=3,
        emoguard_interval=3,
    )

    print("\nSTEP 1: Generate or reuse baseline")

    generate_or_reuse_baselines(
        personas=personas,
        replicates=1,
        baseline_version=config.version,
    )

    print("\nSTEP 2: Register disposable experiment")

    register_experiment(
        config=config,
        personas=personas,
    )

    session = get_session()

    try:

        # Retrieve the pair specifically through this config.
        from storage.models import ExperimentConfig

        db_config = session.scalar(
            select(ExperimentConfig).where(
                ExperimentConfig.config_id == CONFIG_ID
            )
        )

        pair = session.scalar(
            select(ExperimentPair).where(
                ExperimentPair.config_db_id == db_config.id
            )
        )

        if pair is None:
            raise RuntimeError("Test pair was not registered.")

        pair_id = pair.pair_id

        off_run = next(
            run for run in pair.runs
            if run.condition == "off"
        )

        # Simulate a run that was interrupted two hours ago.
        off_run.status = "running"
        off_run.started_at = (
            datetime.now(timezone.utc).replace(tzinfo=None)
            - timedelta(hours=2)
        )
        pair.status = "running"

        off_run_id = off_run.run_id

        session.commit()

    finally:
        session.close()

    print("\nSTEP 3: Verify dry-run recovery")

    stale_ids = recover_stale_runs(
        config_id=CONFIG_ID,
        stale_after_minutes=60,
        dry_run=True,
    )

    assert off_run_id in stale_ids

    off_run = get_run_record(pair_id, "off")
    assert off_run.status == "running"

    print("Dry-run passed: database remains unchanged.")

    print("\nSTEP 4: Apply recovery")

    recovered_ids = recover_stale_runs(
        config_id=CONFIG_ID,
        stale_after_minutes=60,
        dry_run=False,
    )

    assert off_run_id in recovered_ids

    off_run = get_run_record(pair_id, "off")
    assert off_run.status == "failed"

    print("Recovery passed: stale run marked as failed.")

    print("\nSTEP 5: Retry the experiment")

    run_batch(
        config=config,
        limit_pairs=1,
    )

    off_run = get_run_record(pair_id, "off")
    on_run = get_run_record(pair_id, "on")

    assert off_run.status == "completed"
    assert on_run.status == "completed"

    print("\nCrash recovery test passed!")
    print("OFF:", off_run.status)
    print("ON:", on_run.status)


if __name__ == "__main__":
    main()