from assessment.pdi import PDI_ITEMS, calculate_score

# All experiences unendorsed
responses = [
    {
        "endorsed": False,
        "distress": 0,
        "preoccupation": 0,
        "conviction": 0,
    }
    for _ in PDI_ITEMS
]

assert len(PDI_ITEMS) == 21
assert calculate_score(responses) == {
    "endorsement_count": 0,
    "distress_sum": 0,
    "preoccupation_sum": 0,
    "conviction_sum": 0,
    "grand_total": 0,
}

# One endorsed experience
responses[0] = {
    "endorsed": True,
    "distress": 2,
    "preoccupation": 3,
    "conviction": 4,
}

scores = calculate_score(responses)

assert scores["endorsement_count"] == 1
assert scores["distress_sum"] == 2
assert scores["preoccupation_sum"] == 3
assert scores["conviction_sum"] == 4
assert scores["grand_total"] == 10

print("PDI scoring tests passed!")
