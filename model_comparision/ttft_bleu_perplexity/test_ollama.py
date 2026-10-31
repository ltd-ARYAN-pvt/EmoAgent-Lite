
import requests
import time
import json
import statistics

OLLAMA_URL = "http://localhost:11434/api/generate"

MODELS = {
    "Qwen 3.5": "qwen3.5:9b",
    "Llama 3.1": "llama3.1:8b"
}

PROMPT = "What is machine learning?"
NUM_RUNS = 5
NUM_PREDICT = 64


def test_model(model_name, model_tag):
    print(f"\n{'=' * 50}")
    print(f"Testing: {model_name} ({model_tag})")
    print("=" * 50)

    ttft_results = []

    # Run one warm-up request (not included in results)
    print("Running warm-up...")

    warmup_payload = {
        "model": model_tag,
        "prompt": PROMPT,
        "stream": False,
        "think": False,
        "keep_alive": "10m",
        "options": {
            "num_predict": NUM_PREDICT,
            "temperature": 0
        }
    }

    try:
        warmup_response = requests.post(
            OLLAMA_URL,
            json=warmup_payload,
            timeout=600
        )
        warmup_response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Warm-up failed: {e}")
        return

    print("Warm-up completed.")

    # Perform measured runs
    for run in range(1, NUM_RUNS + 1):

        payload = {
            "model": model_tag,
            "prompt": PROMPT,
            "stream": True,
            "think": False,
            "keep_alive": "10m",
            "options": {
                "num_predict": NUM_PREDICT,
                "temperature": 0
            }
        }

        start_time = time.perf_counter()
        first_text_time = None
        answer = ""

        try:
            with requests.post(
                OLLAMA_URL,
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

                    # Record arrival of the first non-empty text chunk
                    if chunk and first_text_time is None:
                        first_text_time = time.perf_counter()

                    answer += chunk

                    if data.get("done"):
                        break

            if first_text_time is not None:
                ttft_ms = (first_text_time - start_time) * 1000
                ttft_results.append(ttft_ms)

                print(f"Run {run}: TTFT = {ttft_ms:.2f} ms")

            else:
                print(f"Run {run}: No text generated.")

        except requests.exceptions.RequestException as e:
            print(f"Run {run} failed: {e}")

    # Display summary
    if ttft_results:
        print("\n--- Results ---")
        print(f"Successful runs: {len(ttft_results)}")
        print(f"Average TTFT: {statistics.mean(ttft_results):.2f} ms")
        print(f"Median TTFT:  {statistics.median(ttft_results):.2f} ms")
        print(f"Minimum TTFT: {min(ttft_results):.2f} ms")
        print(f"Maximum TTFT: {max(ttft_results):.2f} ms")

    else:
        print("No successful measurements.")


if __name__ == "__main__":

    print("OLLAMA MODEL TTFT COMPARISON")
    print(f"Number of measured runs: {NUM_RUNS}")
    print(f"Maximum generated tokens: {NUM_PREDICT}")

    for model_name, model_tag in MODELS.items():
        test_model(model_name, model_tag)

    print("\nTesting completed.")
