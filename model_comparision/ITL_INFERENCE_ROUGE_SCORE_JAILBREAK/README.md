# Ollama Model Comparison: Llama 3.1:8B vs Qwen 3.5:9B

A performance and output-quality comparison of two locally run [Ollama](https://ollama.com) models, **Llama 3.1:8B** and **Qwen 3.5:9B**. The notebook `graph_analysis_of_models.ipynb` takes the measured results, visualises them, and computes a percentage-difference summary between the two models.

---

## Table of Contents

- [What Was Compared](#what-was-compared)
- [Metrics](#metrics)
- [Test Setup](#test-setup)
- [Repository Contents](#repository-contents)
- [Getting Started](#getting-started)
- [Output Files](#output-files)
- [Results Summary](#results-summary)
- [Key Takeaways](#key-takeaways)
- [Limitations](#limitations)

---

## What Was Compared

| | Llama 3.1:8B | Qwen 3.5:9B |
|---|---|---|
| Ollama tag | `llama3.1:8b` | `qwen3.5:9b` |
| Parameters | 8B | 9B |

Each model was evaluated across **two start conditions** and **three test categories**.

### Start conditions

- **Cold**: the model is not yet loaded in memory, so the run includes model loading time.
- **Warm**: the model is already loaded, so loading time is close to zero.

### Test categories

- **Summary**: a text summarisation task, scored against a reference with ROUGE.
- **Jailbreak**: prompts that attempt to bypass the model's safety behaviour.
- **Benign Control**: harmless prompts used as a baseline for the jailbreak category.

ROUGE scores are only computed for the Summary category.

---

## Metrics

| Metric | Unit | Meaning |
|---|---|---|
| **ITL** (Inter-Token Latency) | ms | Average delay between generated tokens. Lower is faster. |
| **Request Time** | seconds | Total time for the request from start to finish. |
| **Load Time** | seconds | Time spent loading the model into memory. |
| **Generation Time** | seconds | Time spent producing the response text. |
| **ROUGE-1** | 0 to 1 | Unigram (single word) overlap with the reference summary. Higher is better. |
| **ROUGE-2** | 0 to 1 | Bigram (two word sequence) overlap with the reference summary. Higher is better. |
| **ROUGE-L** | 0 to 1 | Longest common subsequence overlap with the reference summary. Higher is better. |

For all timing metrics, **lower is better**.

---

## Test Setup

> Fill in the details below so others can reproduce your results.

- **Hardware:** _(CPU / GPU / RAM)_
- **Operating system:** _(e.g. Windows 11, Ubuntu 24.04)_
- **Ollama version:** _(output of `ollama --version`)_
- **Prompts used:** _(number of prompts per category, source of the jailbreak set)_
- **Number of runs averaged:** _(single run or mean of N runs)_
- **Reference summaries used for ROUGE:** _(dataset or source)_

---

## Repository Contents

```
.
├── graph_analysis_of_models.ipynb   # Data, plots, and difference analysis
├── README.md
└── ollama_comparison_graphs/        # Created when the notebook is run
    ├── 01_ITL_Comparison.png
    ├── 02_Request_Time.png
    ├── 03_Loading_Time.png
    ├── 04_Generation_Time.png
    ├── 05_ROUGE_Comparison.png
    ├── 06_Combined_Dashboard.png
    └── experimental_results.csv
```

---

## Getting Started

### Requirements

- Python 3.8+
- Jupyter Notebook or JupyterLab

### Install dependencies

```bash
pip install numpy pandas matplotlib seaborn jupyter
```

### Run the notebook

```bash
jupyter notebook graph_analysis_of_models.ipynb
```

Run all cells. The results are stored directly in the notebook as a Python list, so **Ollama does not need to be running** to reproduce the graphs.

### What the notebook does

1. **Configuration**: sets the plot style and creates the `ollama_comparison_graphs/` output folder.
2. **Experimental data**: loads the measured results into a pandas DataFrame and cleans the labels.
3. **Plots**: draws side-by-side Cold vs Warm bar charts for each timing metric, a ROUGE comparison, and a combined 2x2 dashboard.
4. **Difference analysis**: prints which model is faster in each condition and category, with the percentage gap.
5. **Export**: saves the full table as `experimental_results.csv`.

---

## Output Files

| File | Description |
|---|---|
| `01_ITL_Comparison.png` | Inter-token latency, Cold vs Warm |
| `02_Request_Time.png` | Total request time, Cold vs Warm |
| `03_Loading_Time.png` | Model load time, Cold vs Warm |
| `04_Generation_Time.png` | Text generation time, Cold vs Warm |
| `05_ROUGE_Comparison.png` | ROUGE-1, ROUGE-2 and ROUGE-L for the summary task |
| `06_Combined_Dashboard.png` | All four timing metrics in one figure |
| `experimental_results.csv` | Raw table of every result used in the plots |

All images are saved at 300 DPI.

---

## Results Summary

### Timing, Cold start

| Category | Metric | Llama 3.1:8B | Qwen 3.5:9B | Faster |
|---|---|---|---|---|
| Summary | ITL (ms) | 224.71 | 176.81 | Qwen |
| Summary | Request (s) | 23.87 | 19.59 | Qwen |
| Summary | Load (s) | 17.20 | 14.40 | Qwen |
| Summary | Generation (s) | 5.53 | 4.23 | Qwen |
| Jailbreak | ITL (ms) | 147.01 | 169.12 | Llama |
| Jailbreak | Request (s) | 20.17 | 27.43 | Llama |
| Jailbreak | Load (s) | 8.88 | 12.26 | Llama |
| Jailbreak | Generation (s) | 10.80 | 14.48 | Llama |
| Benign Control | ITL (ms) | 145.68 | 168.33 | Llama |
| Benign Control | Request (s) | 26.51 | 32.96 | Llama |
| Benign Control | Load (s) | 8.68 | 12.26 | Llama |
| Benign Control | Generation (s) | 17.34 | 20.03 | Llama |

### Timing, Warm start

| Category | Metric | Llama 3.1:8B | Qwen 3.5:9B | Faster |
|---|---|---|---|---|
| Summary | ITL (ms) | 151.77 | 169.65 | Llama |
| Summary | Request (s) | 5.76 | 6.21 | Llama |
| Summary | Load (s) | 0.0141 | 0.0257 | Llama |
| Summary | Generation (s) | 3.84 | 4.07 | Llama |
| Jailbreak | ITL (ms) | 149.24 | 168.82 | Llama |
| Jailbreak | Request (s) | 13.53 | 16.92 | Llama |
| Jailbreak | Load (s) | 0.0130 | 0.0199 | Llama |
| Jailbreak | Generation (s) | 11.19 | 14.41 | Llama |
| Benign Control | ITL (ms) | 145.03 | 169.41 | Llama |
| Benign Control | Request (s) | 19.62 | 22.68 | Llama |
| Benign Control | Load (s) | 0.0224 | 0.0166 | Qwen |
| Benign Control | Generation (s) | 17.26 | 20.16 | Llama |

### Summary quality (ROUGE)

| Condition | Model | ROUGE-1 | ROUGE-2 | ROUGE-L |
|---|---|---|---|---|
| Cold | Llama 3.1:8B | 0.5500 | **0.2085** | 0.4643 |
| Cold | Qwen 3.5:9B | **0.5657** | 0.1799 | **0.4771** |
| Warm | Llama 3.1:8B | 0.5621 | **0.2141** | 0.4744 |
| Warm | Qwen 3.5:9B | **0.5657** | 0.1799 | **0.4771** |

> The "Difference" percentages printed by the notebook are calculated relative to Llama's value: `|Llama - Qwen| / Llama x 100`.

---

## Key Takeaways

- **Llama 3.1:8B is faster in most cases.** It wins on inter-token latency, request time, and generation time in every test except the cold-start summary task.
- **Qwen 3.5:9B wins the cold-start summary run** on all four timing metrics, which is the one case where it clearly beats Llama on speed.
- **Llama's cold-start summary run is an outlier.** Its ITL (224.71 ms) and load time (17.20 s) are noticeably higher than in its other cold runs (about 146 to 147 ms ITL and about 8.7 to 8.9 s load). This is likely a first-load effect, so it is worth re-running before drawing conclusions from it.
- **Warm starts remove loading overhead for both models.** Load time drops from several seconds to roughly 0.01 to 0.03 seconds.
- **Qwen is steadier on ITL.** Its inter-token latency stays between about 168 and 177 ms across all runs, while Llama's ranges from about 145 to 225 ms.
- **Summary quality is close.** Qwen scores slightly higher on ROUGE-1 and ROUGE-L, while Llama scores higher on ROUGE-2. The differences are small.
- **Jailbreak and Benign Control behaviour is not scored here.** Only timing was measured for those categories, so this comparison does not say which model is safer.

---

## Limitations

- Results appear to be a single value per model, condition, and category, with no error bars or repeated-run variance. Small differences may not be statistically meaningful.
- ROUGE measures word overlap, not factual accuracy or readability.
- Timings depend heavily on hardware, quantisation, and Ollama configuration, so they may not carry over to other machines.
- Jailbreak responses were timed but not evaluated for whether the model refused or complied.
- The two models differ in size (8B vs 9B parameters), so speed differences are partly expected.

---

## License

_Add your license here (e.g. MIT)._
