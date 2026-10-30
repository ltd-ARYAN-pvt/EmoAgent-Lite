import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from datetime import datetime, timezone
from uuid import uuid4

from models import (
    Persona,
    BaselineAssessment,
    ExperimentConfig,
    ExperimentPair,
    ExperimentRun,
    ExperimentArtifact,
)

from schemas import ExperimentConfigCreate, ExperimentRunResult


def calculate_hash(data: dict[str, Any]) -> str:
    serialized = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def validate_baseline_record(record: dict) -> None:
    """Validate the PHQ-9 record using the existing V3 data structure."""

    if not isinstance(record, dict):
        raise ValueError("Baseline assessment must be a dictionary.")

    if record.get("instrument") != "PHQ-9":
        raise ValueError("Expected a PHQ-9 record.")

    if record.get("phase") != "baseline":
        raise ValueError("Expected a baseline assessment record.")

    if record.get("data_type") != "synthetic":
        raise ValueError("Expected synthetic assessment data.")

    responses = record.get("responses")

    if not isinstance(responses, list) or len(responses) != 9:
        raise ValueError("PHQ-9 must contain exactly 9 responses.")

    if any(
        type(value) is not int or not 0 <= value <= 3
        for value in responses
    ):
        raise ValueError("PHQ-9 responses must be integers from 0 to 3.")

    expected_total = sum(responses)
    scores = record.get("scores")

    if not isinstance(scores, dict):
        raise ValueError("PHQ-9 record is missing its scores.")

    if scores.get("total") != expected_total:
        raise ValueError(
            "PHQ-9 total does not match the response vector."
        )


def get_or_create_persona(
    session: Session,
    persona: dict[str, Any],
) -> Persona:
    persona_id = persona.get("id")

    if not isinstance(persona_id, str) or not persona_id:
        raise ValueError("Persona must contain a non-empty string ID.")

    profile_hash = calculate_hash(persona)

    existing = session.scalar(
        select(Persona).where(Persona.persona_id == persona_id)
    )

    if existing is not None:
        if existing.profile_hash != profile_hash:
            raise ValueError(
                f"Persona '{persona_id}' has changed since it was stored. "
                "Use a new benchmark/configuration version rather than "
                "silently replacing the existing profile."
            )
        return existing

    db_persona = Persona(
        persona_id=persona_id,
        profile_hash=profile_hash,
        profile_json=persona,
    )

    session.add(db_persona)
    session.flush()

    return db_persona


def get_baseline(
    session: Session,
    persona_id: str,
    replicate: int,
    baseline_version: str = "4.1",
) -> BaselineAssessment | None:

    return session.scalar(
        select(BaselineAssessment)
        .join(Persona)
        .where(
            Persona.persona_id == persona_id,
            BaselineAssessment.replicate == replicate,
            BaselineAssessment.baseline_version == baseline_version,
        )
    )


def create_baseline(
    session: Session,
    persona: dict[str, Any],
    replicate: int,
    assessment_record: dict,
    baseline_version: str = "4.1",
) -> BaselineAssessment:
    """
    Store one generated baseline.

    The caller should first use get_baseline() to check whether
    a baseline already exists.
    """

    if type(replicate) is not int or replicate < 1:
        raise ValueError("Replicate must be a positive integer.")

    validate_baseline_record(assessment_record)

    persona_db = get_or_create_persona(session, persona)

    existing = get_baseline(
        session,
        persona["id"],
        replicate,
        baseline_version,
    )

    if existing is not None:
        raise ValueError(
            "Baseline already exists. Retrieve and reuse it instead."
        )

    responses = assessment_record["responses"]
    total_score = assessment_record["scores"]["total"]

    baseline = BaselineAssessment(
        baseline_id=(
            f"{persona['id']}-rep{replicate}-baseline-{baseline_version}"
        ),
        persona_db_id=persona_db.id,
        replicate=replicate,
        baseline_version=baseline_version,
        instrument=assessment_record["instrument"],
        total_score=total_score,
        responses_json=responses,
        assessment_json=assessment_record,
        data_type=assessment_record["data_type"],
    )

    session.add(baseline)
    session.flush()

    return baseline


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------
# EXPERIMENT CONFIGURATION
# ---------------------------------------------------------

def get_config(
    session: Session,
    config_id: str,
) -> ExperimentConfig | None:
    return session.scalar(
        select(ExperimentConfig).where(
            ExperimentConfig.config_id == config_id
        )
    )


def create_config(
    session: Session,
    config_data: dict,
) -> ExperimentConfig:
    """
    Create an immutable experiment configuration.

    Reusing a config_id with different settings is rejected.
    """

    validated = ExperimentConfigCreate.model_validate(config_data)
    data = validated.model_dump()

    existing = get_config(session, data["config_id"])

    if existing is not None:
        if existing.config_hash != data["config_hash"]:
            raise ValueError(
                "Configuration ID already exists with a different hash."
            )
        return existing

    config = ExperimentConfig(**data)

    session.add(config)
    session.flush()

    return config


# ---------------------------------------------------------
# EXPERIMENT PAIRS
# ---------------------------------------------------------

def get_pair(
    session: Session,
    pair_id: str,
) -> ExperimentPair | None:
    return session.scalar(
        select(ExperimentPair).where(
            ExperimentPair.pair_id == pair_id
        )
    )


def create_pair(
    session: Session,
    config_id: str,
    baseline_id: str,
    persona_id: str,
    character_id: str,
    dialogue_style: str,
    replicate: int,
) -> ExperimentPair:
    """
    Create a matched OFF/ON comparison.

    The baseline must belong to the same persona and replicate.
    """

    if dialogue_style not in {"meow", "roar"}:
        raise ValueError("Unsupported dialogue style.")

    if type(replicate) is not int or replicate < 1:
        raise ValueError("Replicate must be a positive integer.")

    config = get_config(session, config_id)

    if config is None:
        raise ValueError(f"Unknown experiment config: {config_id}")

    baseline = session.scalar(
        select(BaselineAssessment).where(
            BaselineAssessment.baseline_id == baseline_id
        )
    )

    if baseline is None:
        raise ValueError(f"Unknown baseline: {baseline_id}")

    if baseline.persona.persona_id != persona_id:
        raise ValueError("Baseline belongs to a different persona.")

    if baseline.replicate != replicate:
        raise ValueError("Baseline belongs to a different replicate.")

    if dialogue_style not in config.dialogue_styles:
        raise ValueError("Dialogue style is not enabled in this config.")

    if replicate > config.replicates:
        raise ValueError("Replicate exceeds configured replicate count.")

    if baseline.baseline_version != config.version:
        raise ValueError(
            "Baseline version does not match experiment configuration."
        )

    existing = session.scalar(
        select(ExperimentPair).where(
            ExperimentPair.config_db_id == config.id,
            ExperimentPair.persona_id == persona_id,
            ExperimentPair.character_id == character_id,
            ExperimentPair.dialogue_style == dialogue_style,
            ExperimentPair.replicate == replicate,
        )
    )

    if existing is not None:
        if existing.baseline_db_id != baseline.id:
            raise ValueError(
                "Existing pair is linked to a different baseline."
            )
        return existing

    pair = ExperimentPair(
        pair_id=str(uuid4()),
        config_db_id=config.id,
        baseline_db_id=baseline.id,
        persona_id=persona_id,
        character_id=character_id,
        dialogue_style=dialogue_style,
        replicate=replicate,
        status="pending",
    )

    session.add(pair)
    session.flush()

    return pair


# ---------------------------------------------------------
# RUN CREATION AND RETRIEVAL
# ---------------------------------------------------------

def get_run(
    session: Session,
    pair_id: str,
    condition: str,
) -> ExperimentRun | None:
    if condition not in {"off", "on"}:
        raise ValueError("Condition must be 'off' or 'on'.")

    return session.scalar(
        select(ExperimentRun)
        .join(ExperimentPair)
        .where(
            ExperimentPair.pair_id == pair_id,
            ExperimentRun.condition == condition,
        )
    )


def create_pair_runs(
    session: Session,
    pair_id: str,
    model_name: str,
    first_condition: str = "off",
) -> list[ExperimentRun]:
    """
    Create exactly two run records: OFF and ON.

    first_condition determines execution order, not run identity.
    """

    if first_condition not in {"off", "on"}:
        raise ValueError("first_condition must be 'off' or 'on'.")

    pair = get_pair(session, pair_id)

    if pair is None:
        raise ValueError(f"Unknown pair: {pair_id}")

    existing = {
        run.condition: run
        for run in pair.runs
    }

    if existing and set(existing) != {"off", "on"}:
        raise ValueError(
            "Pair has an incomplete run structure. Inspect before continuing."
        )

    if existing:
        return [existing[first_condition], existing[
            "on" if first_condition == "off" else "off"
        ]]

    second_condition = "on" if first_condition == "off" else "off"

    first = ExperimentRun(
        run_id=str(uuid4()),
        pair_db_id=pair.id,
        condition=first_condition,
        status="pending",
        execution_order=1,
        model_name=model_name,
    )

    second = ExperimentRun(
        run_id=str(uuid4()),
        pair_db_id=pair.id,
        condition=second_condition,
        status="pending",
        execution_order=2,
        model_name=model_name,
    )

    session.add_all([first, second])
    session.flush()

    return [first, second]


# ---------------------------------------------------------
# RUN LIFECYCLE
# ---------------------------------------------------------

def start_run(
    session: Session,
    run_id: str,
) -> ExperimentRun:
    run = session.scalar(
        select(ExperimentRun).where(
            ExperimentRun.run_id == run_id
        )
    )

    if run is None:
        raise ValueError(f"Unknown run: {run_id}")

    if run.status not in {"pending", "failed"}:
        raise ValueError(
            f"Cannot start run with status '{run.status}'."
        )

    run.status = "running"
    run.started_at = _now()
    run.completed_at = None
    run.error_message = None

    pair = run.pair
    pair.status = "running"

    session.flush()
    return run



def complete_run(
    session: Session,
    run_id: str,
    result_data: dict,
) -> ExperimentRun:
    run = session.scalar(
        select(ExperimentRun).where(
            ExperimentRun.run_id == run_id
        )
    )

    if run is None:
        raise ValueError(f"Unknown run: {run_id}")

    if run.status != "running":
        raise ValueError("Only running experiments can be completed.")

    result = ExperimentRunResult.model_validate(result_data)

    config = run.pair.config

    expected_rounds = (
        list(range(
            config.emoguard_interval,
            config.max_rounds + 1,
            config.emoguard_interval,
        ))
        if run.condition == "on"
        else []
    )

    if result.intervention_rounds != expected_rounds:
        raise ValueError(
            f"Unexpected intervention rounds. "
            f"Expected {expected_rounds}, "
            f"received {result.intervention_rounds}."
        )

    run.initial_score = result.initial_score
    run.final_score = result.final_score
    run.score_delta = result.score_delta

    run.intervention_count = result.intervention_count
    run.intervention_rounds = result.intervention_rounds

    run.status = "completed"
    run.completed_at = _now()

    # Query actual statuses instead of using pair.runs.
    statuses = list(
        session.scalars(
            select(ExperimentRun.status).where(
                ExperimentRun.pair_db_id == run.pair_db_id
            )
        ).all()
    )

    if len(statuses) == 2 and all(
        status == "completed" for status in statuses
    ):
        run.pair.status = "completed"
        run.pair.completed_at = _now()

    elif "completed" in statuses and "failed" in statuses:
        run.pair.status = "partially_failed"

    elif "failed" in statuses:
        run.pair.status = "failed"

    else:
        run.pair.status = "running"

    session.flush()

    return run



def fail_run(
    session: Session,
    run_id: str,
    error_message: str,
) -> ExperimentRun:
    run = session.scalar(
        select(ExperimentRun).where(
            ExperimentRun.run_id == run_id
        )
    )

    if run is None:
        raise ValueError(f"Unknown run: {run_id}")

    if run.status != "running":
        raise ValueError("Only running experiments can be marked failed.")

    run.status = "failed"
    run.error_message = error_message
    run.completed_at = _now()

    # Query current database statuses explicitly.
    statuses = list(
        session.scalars(
            select(ExperimentRun.status).where(
                ExperimentRun.pair_db_id == run.pair_db_id
            )
        ).all()
    )

    if len(statuses) == 2 and all(s == "completed" for s in statuses):
        run.pair.status = "completed"
    elif "completed" in statuses and "failed" in statuses:
        run.pair.status = "partially_failed"
    elif "failed" in statuses:
        run.pair.status = "failed"
    else:
        run.pair.status = "running"

    session.flush()
    return run


# ---------------------------------------------------------
# ARTIFACTS
# ---------------------------------------------------------

def add_artifact(
    session: Session,
    run_id: str,
    artifact_type: str,
    file_path: str,
) -> ExperimentArtifact:
    allowed_types = {
        "transcript",
        "assessment",
        "emoguard_log",
    }

    if artifact_type not in allowed_types:
        raise ValueError("Unsupported artifact type.")

    run = session.scalar(
        select(ExperimentRun).where(
            ExperimentRun.run_id == run_id
        )
    )

    if run is None:
        raise ValueError(f"Unknown run: {run_id}")

    existing = session.scalar(
        select(ExperimentArtifact).where(
            ExperimentArtifact.run_db_id == run.id,
            ExperimentArtifact.artifact_type == artifact_type,
        )
    )

    if existing is not None:
        existing.file_path = file_path
        return existing

    artifact = ExperimentArtifact(
        run_db_id=run.id,
        artifact_type=artifact_type,
        file_path=file_path,
    )

    session.add(artifact)
    session.flush()

    return artifact


# ---------------------------------------------------------
# PAIR STATUS / RESUME HELPERS
# ---------------------------------------------------------

def refresh_pair_status(
    session: Session,
    pair_id: str,
) -> str:
    pair = get_pair(session, pair_id)

    if pair is None:
        raise ValueError(f"Unknown pair: {pair_id}")

    statuses = {run.status for run in pair.runs}

    if statuses == {"completed"} and len(pair.runs) == 2:
        pair.status = "completed"
        pair.completed_at = pair.completed_at or _now()
    elif "running" in statuses:
        pair.status = "running"
    elif "failed" in statuses and "completed" in statuses:
        pair.status = "partially_failed"
    elif "failed" in statuses:
        pair.status = "failed"
    else:
        pair.status = "pending"

    session.flush()
    return pair.status


def get_incomplete_pairs(
    session: Session,
    config_id: str,
) -> list[ExperimentPair]:
    config = get_config(session, config_id)

    if config is None:
        raise ValueError(f"Unknown config: {config_id}")

    return list(
        session.scalars(
            select(ExperimentPair)
            .where(
                ExperimentPair.config_db_id == config.id,
                ExperimentPair.status != "completed",
            )
            .order_by(ExperimentPair.created_at)
        ).all()
    )