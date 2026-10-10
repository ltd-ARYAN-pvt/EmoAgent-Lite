import json
from pathlib import Path

PERSONA_FILE = Path("data/users.json")


def load_personas() -> list[dict]:
    with PERSONA_FILE.open("r", encoding="utf-8") as file:
        personas = json.load(file)

    if not isinstance(personas, list):
        raise ValueError("Expected a JSON array of personas.")

    ids = [persona["id"] for persona in personas]

    if len(ids) != len(set(ids)):
        raise ValueError("Persona IDs must be unique.")

    return personas


def get_persona(persona_id: str) -> dict:
    for persona in load_personas():
        if persona["id"] == persona_id:
            return persona

    raise KeyError(f"Persona not found: {persona_id}")