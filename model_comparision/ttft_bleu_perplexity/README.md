# LLM Performance Evaluation using Ollama

## Overview

This project evaluates and compares locally hosted Large Language Models (LLMs) running through **Ollama**. The evaluation focuses on three widely used performance metrics:

- **TTFT (Time to First Token)** – Measures model response latency.
- **BLEU Score** – Measures similarity between generated responses and reference answers.
- **Perplexity** – Measures the language modeling capability of a model (using Hugging Face checkpoints).

The current implementation compares:

- Llama 3.1 (8B)
- Qwen 3.5 (9B)

The models are configured in `config.py`. :chatgpt-content-reference{index="0"}

---

# Project Structure

```
project/
│
├── dataset/
│   ├── questions.csv
│   └── perplexity_text.txt
│
├── results/
│   ├── ttft_results.csv
│   ├── ttft_summary.csv
│   └── bleu_results.csv
│
├── config.py
├── ttft.py
├── bleu.py
├── perplexity.py
├── main.py
├── requirements.txt
└── README.md
```

---

# Requirements

- Python 3.10+
- Ollama
- Installed LLMs
- Internet connection (only required for Perplexity evaluation using Hugging Face)

Install the dependencies:

```bash
pip install -r requirements.txt
```

Required Python packages include Requests, Pandas, SacreBLEU, Matplotlib, PyTorch, Transformers, Accelerate, and SentencePiece. :chatgpt-content-reference{index="1"}

---

# Install Ollama Models

Check installed models:

```bash
ollama list
```

Example:

```
NAME
llama3.1:latest
qwen3.5:latest
```

If your tags differ, update them in `config.py`.

---

# Start Ollama

Verify the models are running:

```bash
ollama run llama3.1
```

```bash
ollama run qwen3.5
```

---

# Configuration

The project configuration is stored in `config.py`.

Example:

```python
OLLAMA_URL = "http://localhost:11434"

MODELS = {
    "Qwen 3.5": "qwen3.5:9b",
    "Llama 3.1": "llama3.1:8b",
}

NUM_RUNS = 5
MAX_TOKENS = 128
```

:chatgpt-content-reference{index="2"}

---

# Running TTFT Evaluation

Execute:

```bash
python ttft.py
```

The script:

- Performs one warm-up run
- Executes multiple benchmark runs
- Measures:
  - TTFT
  - Prompt evaluation time
  - Generation time
  - Total response time
  - Prompt tokens
  - Generated tokens
- Saves the results in the `results` directory. :chatgpt-content-reference{index="3"}

Generated files:

```
results/ttft_results.csv
results/ttft_summary.csv
```

---

# Running BLEU Evaluation

Execute:

```bash
python bleu.py
```

The script:

- Loads the question-answer dataset
- Generates answers from each model
- Computes Corpus BLEU using SacreBLEU
- Stores every prediction
- Saves the evaluation results as CSV

Dataset:

```
dataset/questions.csv
```

Output:

```
results/bleu_results.csv
```

The BLEU implementation uses SacreBLEU with exponential smoothing and compares generated answers against the reference column in the dataset. :chatgpt-content-reference{index="4"}

---

# Running Perplexity Evaluation

Execute:

```bash
python perplexity.py
```

Unlike TTFT and BLEU, Perplexity cannot be computed directly through the Ollama API because it does not expose token log-probabilities.

Instead, this script loads equivalent Hugging Face checkpoints using the Transformers library to calculate perplexity on a supplied text file. :chatgpt-content-reference{index="5"}

Input file:

```
dataset/perplexity_text.txt
```

---

# Run All Evaluations

Execute:

```bash
python main.py
```

This runs:

1. TTFT Evaluation
2. BLEU Evaluation

Perplexity is executed separately because it requires Hugging Face checkpoints rather than the Ollama API. :chatgpt-content-reference{index="6"}

---

# Output Files

## TTFT

```
results/ttft_results.csv
```

Contains:

- Model
- Run number
- TTFT
- Prompt evaluation duration
- Generation duration
- Total duration
- Token counts

---

## TTFT Summary

```
results/ttft_summary.csv
```

Contains:

- Average TTFT
- Median TTFT
- Minimum TTFT
- Maximum TTFT
- Standard deviation

---

## BLEU Results

```
results/bleu_results.csv
```

Contains:

- Model
- Question
- Reference answer
- Generated answer
- Corpus BLEU score
- Evaluation status

---

# Evaluation Metrics

## TTFT (Time to First Token)

Measures the latency between sending a request and receiving the first generated text chunk.

Lower values indicate faster response time.

---

## BLEU Score

Measures textual similarity between generated responses and reference answers.

Higher BLEU scores indicate closer lexical similarity.

---

## Perplexity

Measures how well a language model predicts a sequence of text.

Lower perplexity indicates better language modeling performance.

---

# Notes

- Run multiple TTFT trials to reduce variability.
- Use identical prompts and generation settings when comparing models.
- BLEU evaluates textual similarity and should not be interpreted as factual correctness.
- Perplexity should only be compared using equivalent model checkpoints and identical evaluation settings. :chatgpt-content-reference{index="7"}

---

# Future Improvements

- ROUGE evaluation
- BERTScore
- Exact Match (EM)
- Throughput benchmarking
- GPU utilization analysis
- Memory usage monitoring
- Automated visualization of evaluation metrics
- Support for additional Ollama models

---
