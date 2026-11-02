from sqlalchemy import select

from storage.database import get_session
from storage.models import (
    ExperimentConfig,
    ExperimentPair,
    ExperimentRun,
    ExperimentArtifact,
)


CONFIG_ID = "emagent-v4.2-artifact-test"


def main():
    session = get_session()

    try:
        config = session.scalar(
            select(ExperimentConfig).where(
                ExperimentConfig.config_id == CONFIG_ID
            )
        )

        assert config is not None, "Configuration not found."

        pairs = list(
            session.scalars(
                select(ExperimentPair).where(
                    ExperimentPair.config_db_id == config.id
                )
            ).all()
        )

        print(f"Pairs: {len(pairs)}")
        assert len(pairs) == 1

        pair = pairs[0]

        runs = list(
            session.scalars(
                select(ExperimentRun).where(
                    ExperimentRun.pair_db_id == pair.id
                )
            ).all()
        )

        assert len(runs) == 2

        for run in runs:
            print(f"\nCondition: {run.condition.upper()}")
            print(f"Status: {run.status}")
            print(f"Initial score: {run.initial_score}")
            print(f"Final score: {run.final_score}")
            print(f"Score delta: {run.score_delta}")
            print(f"Interventions: {run.intervention_count}")
            print(f"Intervention rounds: {run.intervention_rounds}")

            assert run.status == "completed"

            if run.condition == "off":
                assert run.intervention_count == 0
                assert run.intervention_rounds == []

            else:
                assert run.intervention_count == 1
                assert run.intervention_rounds == [3]

            artifacts = list(
                session.scalars(
                    select(ExperimentArtifact).where(
                        ExperimentArtifact.run_db_id == run.id
                    )
                ).all()
            )

            artifact_types = {
                artifact.artifact_type
                for artifact in artifacts
            }

            print(f"Artifacts: {sorted(artifact_types)}")

            assert artifact_types == {
                "transcript",
                "assessment",
                "emoguard_log",
            }

        print("\nAll batch result checks passed!")

    finally:
        session.close()


if __name__ == "__main__":
    main()