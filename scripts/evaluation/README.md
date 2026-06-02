# MediaWiki Code2Code Search - Evaluation & Baselines

This directory contains scripts and configuration files for evaluating the performance (precision, latency, and baseline comparison) of the MediaWiki Code2Code Search engine.

## Directory Contents

*   **`benchmark_latency.py`**: Benchmarks retrieval latency and collects the top-10 search results for neural retrieval.
*   **`build_bm25_index.py`**: Tokenizes the corpus from SQLite and builds/caches the BM25 baseline index.
*   **`benchmark_bm25.py`**: Runs the evaluation queries against the cached BM25 baseline and stores the top-10 results.
*   **`evaluation_queries.json`**: Preprocessed evaluation queries extracted automatically from the manuscript's LaTeX definition.
*   **`evaluation_results.json`**: The saved top-10 results for neural retrieval.
*   **`bm25_results.json`**: The saved top-10 results for the BM25 baseline.

---

## 1. Neural Retrieval Benchmarking (`benchmark_latency.py`)

This script extracts the 28 evaluation queries from the LaTeX file `manuscript/evaluation_queries.tex`, saves them to a clean JSON file (`evaluation_queries.json`), and benchmarks the API. It also collects the top-10 results returned by the search endpoint for subsequent manual P@10 precision assessment.

### Usage

Run against a local or live API endpoint:

```bash
# Run against the default live endpoint (https://code2codesearch.toolforge.org/search)
python scripts/evaluation/benchmark_latency.py

# Run against a local development endpoint (e.g. running on port 8000)
python scripts/evaluation/benchmark_latency.py --url http://127.0.0.1:8000/search --runs 1
```

### Options

*   `--url`: Target API search endpoint.
*   `--runs`: Number of repetitions per query to calculate mean/median latencies (default: 7).
*   `--plot`: Path to save the horizontal box-and-whisker plot chart (default: `latency_boxplot.png`).
*   `--queries-json`: Custom path to load/save the preprocessed queries JSON.
*   `--tex-path`: Custom path to locate the source LaTeX queries document.
*   `--save-results`: Custom path to save the retrieval results JSON (default: `scripts/evaluation/evaluation_results.json`).

---

## 2. BM25 Baseline Evaluation

To evaluate the semantic search retrieval against a traditional term-frequency keyword search baseline, we implement a BM25 baseline using the `rank-bm25` package.

### Step 2a: Build the BM25 Index (`build_bm25_index.py`)

This script loads the corpus of over 1.2 million functions from the SQLite metadata database, tokenizes each code block, builds the BM25 index, and serializes (caches) it to `backend/bm25_index.pkl`. 

*Note: Building this index takes about 1.5 minutes and requires around 4-6 GB of RAM. Caching allows the query benchmark to run instantly on subsequent executions.*

```bash
python scripts/evaluation/build_bm25_index.py
```

### Step 2b: Run the BM25 Benchmark (`benchmark_bm25.py`)

This script loads the preprocessed evaluation queries and the cached BM25 index, runs the queries, retrieves the top-10 matches, collects their database metadata, and dumps them to `bm25_results.json` matching the neural search output schema.

```bash
python scripts/evaluation/benchmark_bm25.py
```

This output file (`bm25_results.json`) can be compared directly with `evaluation_results.json` for human judges' manual P@10 annotations.
