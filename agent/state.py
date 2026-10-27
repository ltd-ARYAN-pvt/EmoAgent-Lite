from typing import Annotated, Any
from typing_extensions import TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ChatState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    topic: str
    response_count: int
    max_responses: int

class ExperimentState(TypedDict, total=False):
    experiment_id: str
    persona: dict[str, Any]
    character_profile: dict[str, Any]
    dialogue_style: str

    messages: Annotated[list[AnyMessage], add_messages]
    simulated_state: dict[str, Any]

    assessment_phase: str
    current_question_index: int
    current_assessment_responses: list[int]

    baseline_responses: list[int]
    baseline_score: int

    followup_responses: list[int]
    followup_score: int
    score_delta: int

    round_count: int
    max_rounds: int
    experiment_result: dict[str, Any]