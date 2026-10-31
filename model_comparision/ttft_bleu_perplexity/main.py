import subprocess
import sys

if __name__ == "__main__":
    print("Running TTFT evaluation...")
    subprocess.run([sys.executable, "ttft.py"], check=True)
    print("\nRunning BLEU evaluation...")
    subprocess.run([sys.executable, "bleu.py"], check=True)
    print("\nTTFT and BLEU evaluations finished. Perplexity requires compatible HF checkpoints; see perplexity.py.")
