
from datetime import datetime
from typing import Any

from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    CheckConstraint,
    JSON,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    persona_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    profile_hash: Mapped[str] = mapped_column(String(64), index=True)
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    baselines: Mapped[list["BaselineAssessment"]] = relationship(
        back_populates="persona"
    )


class ExperimentConfig(Base):
    __tablename__ = "experiment_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    config_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )
    experiment_name: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(30))

    model_name: Mapped[str] = mapped_column(String(150))
    model_parameters: Mapped[dict[str, Any]] = mapped_column(JSON)

    max_rounds: Mapped[int] = mapped_column(Integer)
    replicates: Mapped[int] = mapped_column(Integer)
    dialogue_styles: Mapped[list[str]] = mapped_column(JSON)
    assessments: Mapped[list[str]] = mapped_column(JSON)

    emoguard_interval: Mapped[int] = mapped_column(Integer)

    config_hash: Mapped[str] = mapped_column(String(64), index=True)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    pairs: Mapped[list["ExperimentPair"]] = relationship(
        back_populates="config"
    )



class BaselineAssessment(Base):
    __tablename__ = "baseline_assessments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    baseline_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )

    persona_db_id: Mapped[int] = mapped_column(
        ForeignKey("personas.id", ondelete="RESTRICT")
    )

    replicate: Mapped[int] = mapped_column(Integer)
    baseline_version: Mapped[str] = mapped_column(String(30))

    instrument: Mapped[str] = mapped_column(
        String(50), default="PHQ-9"
    )
    total_score: Mapped[int] = mapped_column(Integer)
    responses_json: Mapped[list[int]] = mapped_column(JSON)

    # Preserve the complete record produced by assessment/nodes.py
    assessment_json: Mapped[dict[str, Any]] = mapped_column(JSON)

    data_type: Mapped[str] = mapped_column(
        String(30), default="synthetic"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    persona: Mapped["Persona"] = relationship(
        back_populates="baselines"
    )

    pairs: Mapped[list["ExperimentPair"]] = relationship(
        back_populates="baseline"
    )

    __table_args__ = (
        UniqueConstraint(
            "persona_db_id",
            "replicate",
            "baseline_version",
            name="uq_persona_replicate_baseline_version",
        ),
        CheckConstraint(
            "replicate >= 1",
            name="ck_baseline_replicate_positive",
        ),
        CheckConstraint(
            "total_score >= 0 AND total_score <= 27",
            name="ck_baseline_phq9_range",
        ),
    )



class ExperimentPair(Base):
    __tablename__ = "experiment_pairs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    pair_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )

    config_db_id: Mapped[int] = mapped_column(
        ForeignKey("experiment_configs.id", ondelete="RESTRICT")
    )
    baseline_db_id: Mapped[int] = mapped_column(
        ForeignKey("baseline_assessments.id", ondelete="RESTRICT")
    )

    persona_id: Mapped[str] = mapped_column(String(100), index=True)
    character_id: Mapped[str] = mapped_column(String(100))
    dialogue_style: Mapped[str] = mapped_column(String(30))
    replicate: Mapped[int] = mapped_column(Integer)

    # pending, running, completed, partially_failed, failed
    status: Mapped[str] = mapped_column(
        String(30), default="pending", index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    config: Mapped["ExperimentConfig"] = relationship(
        back_populates="pairs"
    )
    baseline: Mapped["BaselineAssessment"] = relationship(
        back_populates="pairs"
    )
    runs: Mapped[list["ExperimentRun"]] = relationship(
        back_populates="pair", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "config_db_id",
            "persona_id",
            "character_id",
            "dialogue_style",
            "replicate",
            name="uq_experiment_pair_dimensions",
        ),
        CheckConstraint(
            "replicate >= 1",
            name="ck_pair_replicate_positive",
        ),
    )


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    run_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )
    pair_db_id: Mapped[int] = mapped_column(
        ForeignKey("experiment_pairs.id", ondelete="CASCADE")
    )

    # off or on
    condition: Mapped[str] = mapped_column(String(10))

    # pending, running, completed, failed
    status: Mapped[str] = mapped_column(
        String(30), default="pending", index=True
    )

    execution_order: Mapped[int] = mapped_column(Integer)

    initial_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    final_score: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    score_delta: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    intervention_count: Mapped[int] = mapped_column(
        Integer, default=0
    )
    intervention_rounds: Mapped[list[int]] = mapped_column(
        JSON, default=list
    )

    model_name: Mapped[str] = mapped_column(String(150))
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    pair: Mapped["ExperimentPair"] = relationship(
        back_populates="runs"
    )
    artifacts: Mapped[list["ExperimentArtifact"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "pair_db_id",
            "condition",
            name="uq_pair_condition",
        ),
        CheckConstraint(
            "condition IN ('off', 'on')",
            name="ck_run_condition",
        ),
        CheckConstraint(
            "intervention_count >= 0",
            name="ck_intervention_count",
        ),
    )


class ExperimentArtifact(Base):
    __tablename__ = "experiment_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    run_db_id: Mapped[int] = mapped_column(
        ForeignKey("experiment_runs.id", ondelete="CASCADE")
    )

    artifact_type: Mapped[str] = mapped_column(String(50))
    file_path: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    run: Mapped["ExperimentRun"] = relationship(
        back_populates="artifacts"
    )

    __table_args__ = (
        UniqueConstraint(
            "run_db_id",
            "artifact_type",
            name="uq_run_artifact_type",
        ),
    )