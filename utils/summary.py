def print_experiment_summary(
    experiment_result: dict,
    enabled_assessments: list[str],
) -> None:
    records = experiment_result.get("assessment_records", {})

    print("\n========== EXPERIMENT SUMMARY ==========")

    # PHQ-9 summary
    baseline_phq9 = records.get("baseline", {}).get("phq9", {})
    followup_phq9 = records.get("followup", {}).get("phq9", {})

    if baseline_phq9 and followup_phq9:
        baseline_score = baseline_phq9["scores"]["total"]
        followup_score = followup_phq9["scores"]["total"]
        delta = followup_score - baseline_score

        print("\nPHQ-9")
        print(f"  Baseline: {baseline_score}/27")
        print(f"  Follow-up: {followup_score}/27")
        print(f"  Score change: {delta:+d} points")

        if delta > 0:
            print("  Direction: Increased")
        elif delta < 0:
            print("  Direction: Decreased")
        else:
            print("  Direction: Unchanged")
    else:
        print("\nPHQ-9 records are missing.")

    # PDI summary, only when enabled
    if "pdi" in enabled_assessments:
        baseline_pdi = records.get("baseline", {}).get("pdi", {})
        followup_pdi = records.get("followup", {}).get("pdi", {})

        if baseline_pdi and followup_pdi:
            print("\nPDI-21 TOPIC-PROTOTYPE")
            print("  (Synthetic responses; non-standardized administration)")

            labels = {
                "endorsement_count": "Endorsement count",
                "distress_sum": "Distress",
                "preoccupation_sum": "Preoccupation",
                "conviction_sum": "Conviction",
                "grand_total": "Grand total",
            }

            baseline_scores = baseline_pdi["scores"]
            followup_scores = followup_pdi["scores"]

            for key, label in labels.items():
                before = baseline_scores[key]
                after = followup_scores[key]
                print(
                    f"  {label}: {before} -> {after} "
                    f"(change: {after - before:+d})"
                )
        else:
            print("\nPDI was enabled, but baseline/follow-up records are missing.")

    print("\n========================================")