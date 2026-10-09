
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from agent import build_graph
from llm.provider import get_llm


def main():
    load_dotenv()

    llm = get_llm()
    graph = build_graph(llm)

    topic = input("Enter a discussion topic: ").strip()
    if not topic:
        print("Please enter a non-empty topic.")
        return

    try:
        max_responses = int(
            input("Number of agent replies (default 8): ").strip() or "8"
        )
    except ValueError:
        print("Please enter a valid integer.")
        return

    if max_responses < 1:
        print("The number of replies must be at least 1.")
        return

    initial_state = {
        "messages": [
            HumanMessage(
                content=f"Discuss this topic: {topic}",
                name="User",
            )
        ],
        "topic": topic,
        "response_count": 0,
        "max_responses": max_responses,
    }

    print("\n--- EmoAgent Lite ---\n")

    for update in graph.stream(
        initial_state,
        stream_mode="updates",
    ):
        for state_update in update.values():
            for message in state_update.get("messages", []):
                print(f"{message.name}: {message.content}\n")

    print("--- Conversation complete ---")


if __name__ == "__main__":
    main()