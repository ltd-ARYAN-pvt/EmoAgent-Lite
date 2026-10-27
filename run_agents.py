from uuid import uuid4
from dotenv import load_dotenv

from agent.graph import build_graph
from data.persona_loader import get_persona
from llm.provider import get_llm
from pathlib import Path
import json


def main():
    load_dotenv()

    persona_id = input("Persona ID (default 1-1): ").strip() or "1-1"
    character_id = input("Character ID (default sukuna): ").strip() or "sukuna"
    style_input = (input("Dialogue style: Meow or Roar (default Meow): ").strip().lower())
    dialogue_style = style_input or "meow"
    if dialogue_style not in {"meow", "roar"}:
        print("Invalid style. Choose 'meow' or 'roar'.")
        return

    try:
        max_rounds = int(
            input("Conversation rounds (default 3): ").strip() or "3"
        )
    except ValueError:
        print("Please enter a valid integer.")
        return

    if max_rounds < 1:
        print("Conversation rounds must be at least 1.")
        return

    persona = get_persona(persona_id)

    project_root = Path(__file__).resolve().parent
    character_path = (
        project_root / "data" / "characters" / f"{character_id}.json"
    )

    with character_path.open(encoding="utf-8") as file:
        character_profile = json.load(file)

    # Ensure the provider sees environment variables loaded from .env.
    get_llm()

    initial_state = {
        "experiment_id": str(uuid4()),
        "persona": persona,
        "character_profile": character_profile,
        "dialogue_style": dialogue_style,
        "messages": [],
        "simulated_state": {
            "mood": "neutral",
            "distress_level": 5,
            "perceived_stress": 5,
            "recent_experiences": [],
            "current_interpretation": "The conversation has not started yet.",
        },
        "assessment_phase": "baseline",
        "current_question_index": 0,
        "current_assessment_responses": [],
        "baseline_responses": [],
        "followup_responses": [],
        "round_count": 0,
        "max_rounds": max_rounds,
    }

    graph = build_graph()

    print("\n--- EmoAgent Lite V3 experiment ---\n")

    final_results = {}

    for update in graph.stream(initial_state, stream_mode="updates"):
        for node_name, node_update in update.items():
            print(f"[{node_name}]")

            for message in node_update.get("messages", []):
                print(f"{message.name}: {message.content}\n")

            #--> Capture assessment and manager results.
            final_results.update(node_update)

    print("\n--- Experiment complete ---")

    print("\n========== EXPERIMENT SUMMARY ==========")

    if "baseline_responses" in final_results:
        print(f"Baseline PHQ-9: {sum(final_results['baseline_responses'])}/27")

    if "followup_responses" in final_results:
        print(f"Follow-up PHQ-9: {sum(final_results['followup_responses'])}/27")

    if "score_delta" in final_results:
        delta = final_results["score_delta"]
        print(f"Score change: {delta:+d} points")

        if delta > 0:
            print("Direction: Increased")
        elif delta < 0:
            print("Direction: Decreased")
        else:
            print("Direction: Unchanged")

    print("========================================")


if __name__ == "__main__":
    main()