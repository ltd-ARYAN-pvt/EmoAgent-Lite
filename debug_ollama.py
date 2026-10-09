from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0.7,
    num_predict=256,
)

tests = [
    [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Reply in one sentence: Hello!"),
    ],
    [
        SystemMessage(content=(
            "You are Agent B, a critical but respectful thinker. "
            "Always respond with a useful paragraph."
        )),
        HumanMessage(content=(
            "Agent A asks: What challenges do working professionals "
            "face in achieving work-life balance? Give a thoughtful "
            "response in 3-4 sentences."
        )),
    ],
]

for i, messages in enumerate(tests, start=1):
    print(f"\n--- Test {i} ---")
    try:
        response = llm.invoke(messages)
        print("Content:", repr(response.content))
        print("Metadata:", response.response_metadata)
        print("Additional kwargs:", response.additional_kwargs)
    except Exception as exc:
        print(type(exc).__name__, str(exc))