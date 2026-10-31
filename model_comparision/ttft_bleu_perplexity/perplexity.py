"""Calculate perplexity with Hugging Face causal language models.

IMPORTANT:
- Ollama's ordinary /api/generate endpoint does not expose token log-probabilities.
- Therefore this script uses Hugging Face model checkpoints, not the Ollama HTTP API.
- Set HF_MODELS below to compatible Hugging Face checkpoint IDs for the exact
  model variants you want to evaluate. The checkpoints may be large.
- Do not compare unlike model variants and call the result an apples-to-apples test.
"""
import math
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from config import MODELS

# Replace values with the matching Hugging Face checkpoint IDs.
# These are intentionally blank so you don't accidentally evaluate a different model.
HF_MODELS = {
    "Qwen 3.5": "Qwen/Qwen3.5-9B",
    "Llama 3.1": "meta-llama/Llama-3.1-8B-Instruct",
}
TEXT_FILE = "dataset/perplexity_text.txt"

def calculate_perplexity(model_id, text):
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True
    )
    model.eval()
    inputs = tokenizer(text, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs, labels=inputs["input_ids"])
    loss = outputs.loss.item()
    return math.exp(loss)

if __name__ == "__main__":
    text = open(TEXT_FILE, encoding="utf-8").read().strip()
    for name, model_id in HF_MODELS.items():
        if not model_id:
            print(f"Skipping {name}: add its exact Hugging Face checkpoint ID in perplexity.py")
            continue
        try:
            ppl = calculate_perplexity(model_id, text)
            print(f"{name} perplexity: {ppl:.4f}")
        except Exception as exc:
            print(f"Could not evaluate {name}: {exc}")
    print("\nFor a meaningful comparison, use the same text, context handling, and evaluation settings.")
