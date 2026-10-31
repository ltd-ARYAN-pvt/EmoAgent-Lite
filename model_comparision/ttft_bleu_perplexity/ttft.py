
import requests
import time
import json
import pandas as pd
import statistics
import os

from config import OLLAMA_URL, MODELS, NUM_RUNS, MAX_TOKENS

PROMPT = "Explain machine learning in two sentences."

# Keep models loaded between requests
KEEP_ALIVE = "10m"


def run_model(model_tag):

    payload = {
        "model": model_tag,
        "prompt": PROMPT,
        "stream": True,
        "think": False,
        "keep_alive": KEEP_ALIVE,
        "options": {
            "num_predict": MAX_TOKENS,
            "temperature": 0
        }
    }

    start_time = time.perf_counter()
    first_token_time = None
    answer = ""
    final_data = {}

    with requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        stream=True,
        timeout=(10, 600)
    ) as response:

        response.raise_for_status()

        for line in response.iter_lines():

            if not line:
                continue

            data = json.loads(line.decode("utf-8"))

            chunk = data.get("response", "")

            # Measure arrival of first non-empty text
            if chunk:

                if first_token_time is None:
                    first_token_time = time.perf_counter()

                answer += chunk

            if data.get("done"):
                final_data = data
                break

    if first_token_time is None:
        raise RuntimeError(
            f"No answer received from {model_tag}"
        )

    # Client-side TTFT
    ttft_seconds = first_token_time - start_time
    ttft_ms = ttft_seconds * 1000

    # Ollama server timings are reported in nanoseconds
    load_duration = final_data.get("load_duration", 0)
    prompt_eval_duration = final_data.get(
        "prompt_eval_duration", 0
    )
    eval_duration = final_data.get("eval_duration", 0)
    total_duration = final_data.get("total_duration", 0)

    return {
        "ttft_seconds": ttft_seconds,
        "ttft_ms": ttft_ms,
        "answer": answer,
        "load_duration_ms": load_duration / 1_000_000,
        "prompt_eval_duration_ms": prompt_eval_duration / 1_000_000,
        "eval_duration_ms": eval_duration / 1_000_000,
        "total_duration_ms": total_duration / 1_000_000,
        "prompt_tokens": final_data.get("prompt_eval_count", 0),
        "generated_tokens": final_data.get("eval_count", 0)
    }


if __name__ == "__main__":

    os.makedirs("results", exist_ok=True)

    results = []

    for model_name, model_tag in MODELS.items():

        print("\n" + "=" * 50)
        print(f"Testing {model_name}: {model_tag}")
        print("=" * 50)

        # Warm-up (excluded from measurements)
        print("Performing warm-up...")

        try:
            run_model(model_tag)
            print("Warm-up completed.")

        except Exception as e:
            print(f"Warm-up failed: {e}")
            continue

        # Actual measurements
        for i in range(NUM_RUNS):

            try:
                result = run_model(model_tag)

                results.append({
                    "model": model_name,
                    "run": i + 1,
                    "ttft_seconds": result["ttft_seconds"],
                    "ttft_ms": result["ttft_ms"],
                    "load_duration_ms": result["load_duration_ms"],
                    "prompt_eval_duration_ms": result["prompt_eval_duration_ms"],
                    "eval_duration_ms": result["eval_duration_ms"],
                    "total_duration_ms": result["total_duration_ms"],
                    "prompt_tokens": result["prompt_tokens"],
                    "generated_tokens": result["generated_tokens"]
                })

                print(
                    f"Run {i + 1}/{NUM_RUNS}: "
                    f"TTFT = {result['ttft_ms']:.2f} ms"
                )

            except Exception as e:
                print(f"Run {i + 1} failed: {e}")

    # Save individual run results
    if not results:
        print("\nNo successful measurements.")
        raise SystemExit(1)

    df = pd.DataFrame(results)

    df.to_csv(
        "results/ttft_results.csv",
        index=False
    )

    # Generate summary statistics
    summary = df.groupby("model")["ttft_ms"].agg(
        average="mean",
        median="median",
        minimum="min",
        maximum="max",
        standard_deviation="std"
    ).reset_index()

    summary.to_csv(
        "results/ttft_summary.csv",
        index=False
    )

    print("\n========== FINAL TTFT COMPARISON ==========")

    print(
        summary.round(2).to_string(index=False)
    )

    print("\nIndividual results saved to:")
    print("results/ttft_results.csv")

    print("\nSummary results saved to:")
    print("results/ttft_summary.csv")

    print("\nTTFT benchmarking completed!")