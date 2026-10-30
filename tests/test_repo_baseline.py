from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from storage.models import Base
from storage.repository import (
    create_baseline,
    get_baseline,
    validate_baseline_record,
)


def main():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    persona = {
        "id": "test-persona-001",
        "name": "Test Persona",
        "age": 25,
        "background": "Synthetic test profile",
    }

    assessment_record = {
        "instrument": "PHQ-9",
        "instrument_version": "PHQ-9",
        "phase": "baseline",
        "data_type": "synthetic",
        "responses": [1, 2, 1, 0, 1, 2, 0, 1, 0],
        "scores": {"total": 8},
    }

    with SessionLocal() as session:
        try:
            # 1. Validate the assessment record.
            validate_baseline_record(assessment_record)

            # 2. Create and save baseline.
            baseline = create_baseline(
                session=session,
                persona=persona,
                replicate=1,
                assessment_record=assessment_record,
            )

            session.commit()

            print("Baseline created:")
            print("ID:", baseline.baseline_id)
            print("Score:", baseline.total_score)

        except Exception:
            session.rollback()
            raise

    with SessionLocal() as session:
        # 3. Retrieve the same baseline.
        retrieved = get_baseline(
            session=session,
            persona_id="test-persona-001",
            replicate=1,
            baseline_version="4.1",
        )

        assert retrieved is not None
        assert retrieved.total_score == 8
        assert retrieved.responses_json == [1, 2, 1, 0, 1, 2, 0, 1, 0]
        assert retrieved.assessment_json == assessment_record

        print("\nBaseline retrieval successful!")
        print("Full assessment record preserved.")

        # 4. Verify duplicate creation is rejected.
        try:
            create_baseline(
                session=session,
                persona=persona,
                replicate=1,
                assessment_record=assessment_record,
            )
        except ValueError:
            print("Duplicate baseline prevention successful!")
        else:
            raise AssertionError("Duplicate baseline was not rejected.")

    engine.dispose()

    print("\nAll repository tests passed!")


if __name__ == "__main__":
    main()