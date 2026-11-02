from data.persona_loader import load_personas
from storage.database import initialize_database
from batch.baselines import generate_or_reuse_baselines


def main():
    # Initialize SQLite tables.
    initialize_database()

    # Use one existing test persona.
    persona = load_personas()[0]

    print(f"Testing baseline for persona: {persona['id']}")

    # Generate or reuse exactly one baseline.
    baselines = generate_or_reuse_baselines(
        personas=[persona],
        replicates=1,
        baseline_version="4.2",
    )

    record = baselines[(persona["id"], 1)]

    print("\nBaseline smoke test successful!")
    print("Instrument:", record["instrument"])
    print("Responses:", record["responses"])
    print("Total score:", record["scores"]["total"])


if __name__ == "__main__":
    main()