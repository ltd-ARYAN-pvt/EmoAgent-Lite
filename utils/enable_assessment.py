def ask_enabled_assessments() -> list[str]:
    while True:
        choice = input(
            "Include PDI-21 topic-prototype? (0: No, 1: Yes; default: 0): "
        ).strip() or "0"

        if choice == "0":
            return ["phq9"]

        if choice == "1":
            return ["phq9", "pdi"]

        print("Please enter 0 or 1.")

if __name__ == "__main__":
    enabled_assessments = ask_enabled_assessments()