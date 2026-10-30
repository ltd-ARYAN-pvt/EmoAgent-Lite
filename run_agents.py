from uuid import uuid4
from dotenv import load_dotenv

from agent.graph import build_graph
from data.persona_loader import get_persona
from llm.provider import get_llm
from pathlib import Path
import json
from utils import print_experiment_summary, ask_enabled_assessments, print_emoguard_logs

def main():
    load_dotenv()

    persona_id = input("Persona ID (default 1-1): ").strip() or "1-1"
    character_id = input("Character ID (default sukuna): ").strip() or "sukuna"
    style_input = (input("Dialogue style: Meow or Roar (default Meow): ").strip().lower())
    dialogue_style = style_input or "meow"
    emoguard_choice = (
        input("Enable EmoGuard? (0 = OFF, 1 = ON; default = 0): ").strip()
        or "0"
    )

    if emoguard_choice not in {"0", "1"}:
        raise ValueError("Please enter 0 or 1.")

    emoguard_enabled = emoguard_choice == "1"

    if dialogue_style not in {"meow", "roar"}:
        print("Invalid style. Choose 'meow' or 'roar'.")
        return

    try:
        max_rounds = int(
            input("Conversation rounds (max 8 to 10): ").strip() or "8"
        )
    except ValueError:
        print("Please enter a valid integer.")
        return

    if not 1<= max_rounds <=10:
        print("Conversation rounds must be between 1 to 10.")
        return

    try:
        log_interval = int(
            input("Dialog Manager log interval (1 or 2, default 1): ").strip()
            or "1"
        )
    except ValueError:
        print("Please enter 1 or 2.")
        return

    if log_interval not in (1, 2):
        print("Log interval must be 1 or 2.")
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

    enabled_assessments = ask_enabled_assessments()

    initial_state = {
        "experiment_id": str(uuid4()),
        "persona": persona,
        "character_profile": character_profile,
        "dialogue_style": dialogue_style,
        "dialog_manager_log_interval": log_interval,
        "messages": [],
        "simulated_state": {
            "mood": "neutral",
            "distress_level": 5,
            "perceived_stress": 5,
            "recent_experiences": [],
            "current_interpretation": "The conversation has not started yet.",
        },
        "enabled_assessments":enabled_assessments,
        "assessment_phase": "baseline",
        "assessment_records": {},
        "current_question_index": 0,
        "current_assessment_responses": [],
        "round_count": 0,
        "max_rounds": max_rounds,
        "emoguard_enabled": emoguard_enabled,
        "emoguard_log": [],
    }

    graph = build_graph()

    print("\n--- EmoAgent Lite V3 experiment ---\n")

    final_results = {}

    for update in graph.stream(initial_state, stream_mode="updates"):
        for node_name, node_update in update.items():
            print(f"[{node_name}]")

            if "dialog_manager_log" in node_update:
                log = node_update["dialog_manager_log"]
                round_number = log["next_round"]

                if round_number % log_interval == 0:
                    print("\n--- Dialog Manager Decision ---")
                    print(json.dumps(log, indent=2, ensure_ascii=False))
                    print("-------------------------------\n")


            for message in node_update.get("messages", []):
                print(f"{message.name}: {message.content}\n")

            #--> Capture assessment and manager results.
            final_results.update(node_update)

    print("\n--- Experiment complete ---")
    print_experiment_summary(
        experiment_result=final_results,
        enabled_assessments=enabled_assessments,
    )
    print_emoguard_logs(graph_result=final_results)

if __name__ == "__main__":
    main()