from typing import TypedDict

class SimulatedState(TypedDict):
    mood: str
    distress_level: int
    perceived_stress: int
    recent_experiences: list[str]
    current_interpretation: str