from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from models import Base, ExperimentRun
from repository import (
    create_config,
    create_baseline,
    create_pair,
    create_pair_runs,
    start_run,
    complete_run,
    fail_run,
    add_artifact,
    get_baseline,
    get_incomplete_pairs,
)


def main():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    persona = {
        "id": "persona-001",
        "name": "Synthetic Persona",
        "age": 25,
        "background": "Test profile",
    }

    baseline_record = {
        "instrument": "PHQ-9",
        "instrument_version": "PHQ-9",
        "phase": "baseline",
        "data_type": "synthetic",
        "responses": [1, 2, 1, 0, 1, 2, 0, 1, 0],
        "scores": {"total": 8},
    }

    config_data = {
        "config_id": "emagent-v4.1-test",
        "experiment_name": "EmoAgent",
        "version": "4.1",
        "model_name": "test-model",
        "model_parameters": {
            "temperature": 0.7,
        },
        "max_rounds": 10,
        "replicates": 3,
        "dialogue_styles": ["meow", "roar"],
        "assessments": ["phq9"],
        "emoguard_interval": 3,
        "config_hash": "test-config-hash",
        "config_json": {
            "version": "4.1",
            "max_rounds": 10,
            "emoguard_interval": 3,
        },
    }

    with SessionLocal() as session:
        # 1. Save experiment configuration.
        config = create_config(session, config_data)

        # 2. Save baseline.
        baseline = create_baseline(
            session,
            persona,
            replicate=1,
            assessment_record=baseline_record,
            baseline_version="4.1",
        )

        session.flush()

        # 3. Retrieve baseline and verify reuse.
        retrieved = get_baseline(
            session,
            persona_id="persona-001",
            replicate=1,
            baseline_version="4.1",
        )

        assert retrieved is not None
        assert retrieved.id == baseline.id
        assert retrieved.total_score == 8

        # 4. Create a matched pair.
        pair = create_pair(
            session=session,
            config_id=config.config_id,
            baseline_id=baseline.baseline_id,
            persona_id="persona-001",
            character_id="character-001",
            dialogue_style="meow",
            replicate=1,
        )

        # 5. Create OFF and ON run records.
        runs = create_pair_runs(
            session,
            pair.pair_id,
            model_name="test-model",
            first_condition="off",
        )

        assert len(runs) == 2
        assert {run.condition for run in runs} == {"off", "on"}

        off_run = next(r for r in runs if r.condition == "off")
        on_run = next(r for r in runs if r.condition == "on")

        # 6. Complete OFF run.
        start_run(session, off_run.run_id)

        complete_run(
            session,
            off_run.run_id,
            {
                "initial_score": 8,
                "final_score": 7,
                "intervention_count": 0,
                "intervention_rounds": [],
            },
        )

        # 7. Fail ON run, then retry it.
        start_run(session, on_run.run_id)

        fail_run(
            session,
            on_run.run_id,
            "Simulated test failure",
        )

        session.flush()
        assert pair.status == "partially_failed"

        # Retry the same ON run record.
        start_run(session, on_run.run_id)

        complete_run(
            session,
            on_run.run_id,
            {
                "initial_score": 8,
                "final_score": 8,
                "intervention_count": 3,
                "intervention_rounds": [3, 6, 9],
            },
        )

        # 8. Save artifacts.
        add_artifact(
            session,
            off_run.run_id,
            "transcript",
            "results/transcripts/off_test.json",
        )

        add_artifact(
            session,
            on_run.run_id,
            "transcript",
            "results/transcripts/on_test.json",
        )

        add_artifact(
            session,
            on_run.run_id,
            "emoguard_log",
            "results/emoguard_logs/on_test.json",
        )

        session.commit()

        # 9. Verify final state.
        assert pair.status == "completed"
        assert off_run.status == "completed"
        assert on_run.status == "completed"

        assert off_run.score_delta == -1
        assert on_run.score_delta == 0

        assert on_run.intervention_rounds == [3, 6, 9]

        assert len(off_run.artifacts) == 1
        assert len(on_run.artifacts) == 2

        incomplete = get_incomplete_pairs(
            session,
            "emagent-v4.1-test",
        )

        assert len(incomplete) == 0

        # 10. Verify that the database contains exactly two runs.
        all_runs = session.scalars(
            select(ExperimentRun)
        ).all()

        assert len(all_runs) == 2

        print("All V4.1 repository tests passed!")
        print("Configuration:", config.config_id)
        print("Baseline:", baseline.baseline_id)
        print("Pair:", pair.pair_id)
        print("OFF delta:", off_run.score_delta)
        print("ON delta:", on_run.score_delta)
        print("Intervention rounds:", on_run.intervention_rounds)
        print("Pair status:", pair.status)

    engine.dispose()


if __name__ == "__main__":
    main()