from typing import Any, TypedDict


class AssessmentRecord(TypedDict):
    instrument: str
    instrument_version: str
    phase: str
    data_type: str
    responses: list[Any]
    scores: dict[str, Any]