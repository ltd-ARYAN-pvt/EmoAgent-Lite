
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DatabaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PersonaCreate(BaseModel):
    persona_id: str
    profile_hash: str
    profile_json: dict[str, Any]


class ExperimentConfigCreate(BaseModel):
    config_id: str
    experiment_name: str = "EmoAgent"
    version: str = "4.1"

    model_name: str
    model_parameters: dict[str, Any] = Field(default_factory=dict)

    max_rounds: int = 10
    replicates: int = 3
    dialogue_styles: list[str] = ["meow", "roar"]
    assessments: list[str] = ["phq9"]

    emoguard_interval: int = 3

    config_hash: str
    config_json: dict[str, Any]

    @model_validator(mode="after")
    def validate_config(self):
        if self.max_rounds < 1:
            raise ValueError("max_rounds must be positive")

        if self.replicates < 1:
            raise ValueError("replicates must be positive")

        if self.emoguard_interval < 1:
            raise ValueError("emoguard_interval must be positive")

        if not set(self.dialogue_styles).issubset({"meow", "roar"}):
            raise ValueError("Unsupported dialogue style")

        if self.assessments != ["phq9"]:
            raise ValueError("V4.1 supports PHQ-9 only")

        return self



class BaselineAssessmentCreate(BaseModel):
    persona_id: str
    replicate: int = Field(ge=1)
    baseline_version: str = "4.1"

    assessment_record: dict[str, Any]

    @model_validator(mode="after")
    def validate_record(self):
        record = self.assessment_record

        if record.get("instrument") != "PHQ-9":
            raise ValueError("Expected PHQ-9.")

        if record.get("phase") != "baseline":
            raise ValueError("Expected baseline phase.")

        if record.get("data_type") != "synthetic":
            raise ValueError("Expected synthetic data.")

        responses = record.get("responses", [])

        if len(responses) != 9:
            raise ValueError("PHQ-9 requires exactly 9 responses.")

        if any(
            type(x) is not int or not 0 <= x <= 3
            for x in responses
        ):
            raise ValueError("Responses must be integers from 0 to 3.")

        scores = record.get("scores", {})

        if scores.get("total") != sum(responses):
            raise ValueError("PHQ-9 total does not match responses.")

        return self



class ExperimentPairCreate(BaseModel):
    pair_id: str
    config_id: str
    baseline_id: str

    persona_id: str
    character_id: str
    dialogue_style: Literal["meow", "roar"]
    replicate: int = Field(ge=1)


class ExperimentRunCreate(BaseModel):
    run_id: str
    pair_id: str

    condition: Literal["off", "on"]
    execution_order: int = Field(ge=1)
    model_name: str


class ExperimentRunResult(BaseModel):
    initial_score: int = Field(ge=0, le=27)
    final_score: int = Field(ge=0, le=27)

    intervention_count: int = Field(ge=0)
    intervention_rounds: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_result(self):
        if self.intervention_count != len(self.intervention_rounds):
            raise ValueError(
                "intervention_count must match intervention_rounds length"
            )

        if self.intervention_rounds != sorted(set(self.intervention_rounds)):
            raise ValueError(
                "Intervention rounds must be unique and sorted"
            )

        return self

    @property
    def score_delta(self) -> int:
        return self.final_score - self.initial_score


class ExperimentArtifactCreate(BaseModel):
    run_id: str
    artifact_type: Literal[
        "transcript",
        "assessment",
        "emoguard_log",
    ]
    file_path: str