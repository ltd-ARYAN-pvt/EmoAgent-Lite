import json
from pathlib import Path

from dataclasses import replace
from dotenv import load_dotenv

from batch.config import BatchConfig
from batch.baselines import generate_or_reuse_baselines
from batch.registration import register_experiment
from batch.runner import run_batch
from storage.database import initialize_database


def load_pilot_personas(count=5):
    project_root = Path(__file__).resolve().parent.parent
    persona_file = project_root / "data" / "all_users.json"

    with persona_file.open("r", encoding="utf-8") as file:
        personas = json.load(file)

    if not isinstance(personas, list):
        raise ValueError("all_users.json must contain a JSON array.")

    if len(personas) < count:
        raise ValueError(f"Expected at least {count} personas.")

    selected = personas[:count]

    ids = [p["id"] for p in selected]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate persona IDs detected.")

    print("Selected pilot personas:", ids)

    return selected


def main():
    load_dotenv()
    initialize_database()

    config = replace(
        BatchConfig(),
        config_id="emagent-v4.2-pilot-5p-r1-6rounds",
        experiment_name="EmoAgent V4.2 Five-Persona Pilot",
        persona_count=5,
        replicates=1,
        max_rounds=6,
        emoguard_interval=3,
        max_concurrent_runs=1,
        model_name="llama3.1:8b",
    )

    personas = load_pilot_personas(5)

    print("\n========== STEP 1: BASELINES ==========")

    generate_or_reuse_baselines(
        personas=personas,
        replicates=config.replicates,
        baseline_version=config.version,
    )

    print("\n========== STEP 2: REGISTRATION ==========")

    registration = register_experiment(
        config=config,
        personas=personas,
    )

    print("Registration:", registration)

    print("\n========== STEP 3: BATCH EXECUTION ==========")

    run_batch(config=config)

    print("\n========== PILOT EXECUTION PASS FINISHED ==========")
    print("Configuration:", config.config_id)


if __name__ == "__main__":
    main()