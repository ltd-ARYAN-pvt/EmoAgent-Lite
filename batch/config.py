'''This file defines the benchmark settings and validates them before execution.'''
from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass(frozen=True)
class BatchConfig:
    # Experiment identity
    experiment_name: str = "emagent-v4.2-benchmark"
    version: str = "4.2"
    config_id: str = "emagent-v4.2-benchmark"

    # Dataset
    persona_count: int = 100

    character_ids: tuple[str, ...] = (
        "alex",
        "demon",
        "joker",
        "sukuna",
    )

    # Experiment dimensions
    replicates: int = 3
    dialogue_styles: tuple[str, ...] = (
        "meow",
        "roar",
    )

    conditions: tuple[str, ...] = (
        "off",
        "on",
    )

    # Conversation
    max_rounds: int = 10

    # Assessments
    assessments: tuple[str, ...] = ("phq9",)

    # EmoGuard
    emoguard_interval: int = 3

    # Execution
    max_concurrent_runs: int = 1

    # Model configuration
    model_name: str = "llama3.1:8b"
    model_parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.persona_count < 1:
            raise ValueError("persona_count must be positive.")

        if not self.character_ids:
            raise ValueError("At least one character is required.")

        if len(set(self.character_ids)) != len(self.character_ids):
            raise ValueError("Character IDs must be unique.")

        if not set(self.dialogue_styles).issubset({"meow", "roar"}):
            raise ValueError("Unsupported dialogue style.")

        if set(self.conditions) != {"off", "on"}:
            raise ValueError("Both OFF and ON conditions are required.")

        if self.replicates < 1:
            raise ValueError("replicates must be positive.")

        if not 1 <= self.max_rounds <= 10:
            raise ValueError("max_rounds must be between 1 and 10.")

        if self.assessments != ("phq9",):
            raise ValueError("V4.2 batch experiments use PHQ-9 only.")

        if self.emoguard_interval < 1:
            raise ValueError("emoguard_interval must be positive.")

        if self.max_concurrent_runs < 1:
            raise ValueError("max_concurrent_runs must be positive.")

    def to_dict(self) -> dict:
        """Convert configuration into a JSON-compatible dictionary."""
        data = asdict(self)

        # Convert tuples into lists for JSON and database storage.
        data["character_ids"] = list(self.character_ids)
        data["dialogue_styles"] = list(self.dialogue_styles)
        data["conditions"] = list(self.conditions)
        data["assessments"] = list(self.assessments)

        return data