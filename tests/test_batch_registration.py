from dataclasses import replace

from data.persona_loader import load_personas
from storage.database import initialize_database

from batch.config import BatchConfig
from batch.baselines import generate_or_reuse_baselines
from batch.registration import register_experiment


def main():
    initialize_database()

    # Use two personas from the existing test dataset.
    personas = load_personas()[:2]

    # A separate configuration ID keeps this test isolated
    # from the eventual full benchmark.
    config = replace(
        BatchConfig(),
        config_id="emagent-v4.2-registration-test",
        experiment_name="EmoAgent V4.2 Registration Test",
        persona_count=2,
    )

    print("Generating or reusing required baselines...")

    generate_or_reuse_baselines(
        personas=personas,
        replicates=config.replicates,
        baseline_version=config.version,
    )

    print("\nRegistering experiment...")

    result = register_experiment(
        config=config,
        personas=personas,
    )

    print("\nRegistration successful!")
    print(result)


if __name__ == "__main__":
    main()