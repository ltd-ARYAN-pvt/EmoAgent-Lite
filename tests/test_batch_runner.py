from dataclasses import replace

from dotenv import load_dotenv

from data.persona_loader import load_personas
from storage.database import initialize_database

from batch.config import BatchConfig
from batch.baselines import generate_or_reuse_baselines
from batch.registration import register_experiment
from batch.runner import run_batch


def main():
    load_dotenv()
    initialize_database()

    personas = load_personas()[:1]

    config = replace(
        BatchConfig(),
        config_id="emagent-v4.2-artifact-test",
        experiment_name="EmoAgent V4.2 Runner Smoke Test",
        persona_count=1,
        character_ids=("alex",),
        dialogue_styles=("meow",),
        replicates=1,
        max_rounds=3,
        emoguard_interval=3,
    )

    print("Step 1: Generate or reuse baseline")

    generate_or_reuse_baselines(
        personas=personas,
        replicates=config.replicates,
        baseline_version=config.version,
    )

    print("\nStep 2: Register experiment")

    registration = register_experiment(
        config=config,
        personas=personas,
    )

    print(registration)

    print("\nStep 3: Execute one matched pair")

    run_batch(
        config=config,
        limit_pairs=1,
    )

    print("\nRunner smoke test finished!")


if __name__ == "__main__":
    main()