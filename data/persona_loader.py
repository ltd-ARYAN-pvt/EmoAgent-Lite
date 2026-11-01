import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

PERSONA_FILE = DATA_DIR / "users.json"
ALL_PERSONA_FILE = DATA_DIR / "all_users.json"


def load_personas_from_file(
    file_path: Path,
) -> list[dict]:

    with file_path.open("r", encoding="utf-8") as file:
        personas = json.load(file)

    if not isinstance(personas, list):
        raise ValueError("Expected a JSON array of personas.")

    ids = []

    for index, persona in enumerate(personas):
        if not isinstance(persona, dict):
            raise ValueError(
                f"Persona at index {index} must be a dictionary."
            )

        persona_id = persona.get("id")

        if not isinstance(persona_id, str) or not persona_id:
            raise ValueError(
                f"Persona at index {index} has an invalid ID."
            )

        ids.append(persona_id)

    if len(ids) != len(set(ids)):
        raise ValueError("Persona IDs must be unique.")

    return personas


def load_personas() -> list[dict]:
    """Load the small interactive testing dataset."""
    return load_personas_from_file(PERSONA_FILE)


def load_batch_personas(
    persona_count: int = 100,
) -> list[dict]:
    """Load the larger benchmark dataset."""

    if persona_count < 1:
        raise ValueError("persona_count must be positive.")

    personas = load_personas_from_file(ALL_PERSONA_FILE)

    if len(personas) < persona_count:
        raise ValueError(
            f"Requested {persona_count} personas, "
            f"but only {len(personas)} are available."
        )

    # Deterministic selection: use the first N personas.
    # print("Number of personas: ",len(personas))
    return personas[:persona_count]


def get_persona(persona_id: str) -> dict:
    for persona in load_personas():
        if persona["id"] == persona_id:
            return persona

    raise KeyError(f"Persona not found: {persona_id}")