def test_baseline_validation():

    from storage.repository import validate_baseline_record

    record = {
        "instrument": "PHQ-9",
        "instrument_version": "PHQ-9",
        "phase": "baseline",
        "data_type": "synthetic",
        "responses": [1, 2, 1, 0, 1, 2, 0, 1, 0],
        "scores": {"total": 8},
    }

    validate_baseline_record(record)

    print("Baseline validation test passed!")


def test_invalid_baseline():

    from storage.repository import validate_baseline_record

    record = {
        "instrument": "PHQ-9",
        "phase": "baseline",
        "data_type": "synthetic",
        "responses": [1, 2, 1],
        "scores": {"total": 4},
    }

    try:
        validate_baseline_record(record)
    except ValueError:
        print("Invalid baseline correctly rejected!")
    else:
        raise AssertionError("Invalid baseline was accepted.")


if __name__ == "__main__":
    test_baseline_validation()
    test_invalid_baseline()