import os
from langchain_ollama import ChatOllama

def get_llm():
    model_name = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    base_url = os.getenv(
        "OLLAMA_BASE_URL",
        "http://localhost:11434",
    )

    return ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=0.7,
        reasoning=False
    )