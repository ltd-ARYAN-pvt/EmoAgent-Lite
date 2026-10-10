PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things?",
    "Feeling down, depressed, or hopeless?",
    "Trouble falling or staying asleep, or sleeping too much?",
    "Feeling tired or having little energy?",
    "Poor appetite or overeating?",
    "Feeling bad about yourself, or that you are a failure or have let yourself or your family down?",
    "Trouble concentrating on things, such as reading or watching television?",
    "Moving or speaking so slowly that other people could have noticed, or being so fidgety or restless that you have been moving around more than usual?",
    "Thoughts that you would be better off dead or of hurting yourself in some way?",
]

VALID_SCORES = {0, 1, 2, 3}


def calculate_score(responses: list[int]) -> int:
    if len(responses) != 9:
        raise ValueError("Expected exactly 9 PHQ-9 responses.")

    if any(
        type(score) is not int or score not in VALID_SCORES
        for score in responses
    ):
        raise ValueError("Each response must be an integer from 0 to 3.")

    return sum(responses)