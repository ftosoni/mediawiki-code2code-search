import os
import re
import sys
import time
import argparse
import statistics
import requests
import json

# Default settings
DEFAULT_URL = "https://code2codesearch.toolforge.org/search"
DEFAULT_RUNS = 7
DEFAULT_PLOT_PATH = "latency_boxplot.png"

def parse_queries(tex_path):
    """Parse queries and their titles from evaluation_queries.tex."""
    if not os.path.exists(tex_path):
        print(f"Error: {tex_path} not found.")
        sys.exit(1)

    with open(tex_path, "r", encoding="utf-8") as f:
        content = f.read()

    queries = []
    current_title = None
    current_qid = None
    current_lang = None
    in_listing = False
    current_code = []

    def clean_title(title_text):
        # Remove LaTeX macros like \qlang, \texttt, and clean spaces
        title_text = re.sub(r'\\qlang\{.*?\}', '', title_text)
        title_text = re.sub(r'\\texttt\{([^}]+)\}', r'\1', title_text)
        title_text = re.sub(r'[\s~]+', ' ', title_text)
        # Normalize double dashes or long dashes
        title_text = title_text.replace("—", "-").replace("–", "-")
        # Remove leading QID if present in clean title (like A1 - or A1 -- or A1)
        title_text = re.sub(r'^[A-Z]\d+\s*[-–—]*\s*', '', title_text)
        return title_text.strip(" - \t\n")

    for line in content.splitlines():
        if line.startswith(r"\subsection*"):
            match = re.search(r'\\subsection\*\{(.+)\}', line)
            if match:
                raw_title = match.group(1)
                # Extract QID from raw title
                qid_match = re.match(r'^([A-Z]\d+)', raw_title)
                current_qid = qid_match.group(1) if qid_match else "Q"
                # Extract language from \qlang macro
                lang_match = re.search(r'\\qlang\{([^}]+)\}', raw_title)
                if lang_match:
                    current_lang = lang_match.group(1).strip("()")
                else:
                    current_lang = None
                current_title = clean_title(raw_title)
        elif r"\begin{lstlisting}" in line:
            in_listing = True
            current_code = []
        elif r"\end{lstlisting}" in line:
            in_listing = False
            if current_title and current_code:
                code_text = "\n".join(current_code)
                category = current_qid[0] if current_qid and current_qid != "Q" else "Unknown"
                queries.append({
                    "id": current_qid or "Q",
                    "category": category,
                    "title": current_title,
                    "language": current_lang,
                    "code": code_text
                })
                current_title = None
                current_qid = None
                current_lang = None
                current_code = []
        elif in_listing:
            current_code.append(line)

    return queries

def save_queries_to_json(queries, json_path):
    """Save extracted queries to a JSON file."""
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2, ensure_ascii=False)

def run_benchmark(queries, url, runs, save_results_path=None):
    """Run benchmark against the target search API url."""
    print(f"Starting latency benchmark against: {url}")
    print(f"Number of queries: {len(queries)}")
    print(f"Repetitions per query: {runs}")
    print("=" * 60)

    results = {}
    evaluation_records = []
    
    headers = {
        "User-Agent": "MediaWiki-Code2Code-Benchmark/1.0 (https://github.com/ftosoni/mediawiki-code2code-search)"
    }

    # Pre-heat the connection
    print("Pre-heating connection...")
    try:
        requests.post(url, json={
            "query": "preheat connection",
            "top_k": 1,
            "repo_group": ["all"],
            "type_filter": ["all"],
            "language_filter": ["all"]
        }, headers=headers, timeout=5*60)
    except Exception as e:
        print(f"Warning during preheat: {e}")

    for idx, q in enumerate(queries, 1):
        # Safe title printing for Windows consoles
        safe_title = q['title'].encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
        print(f"[{idx}/{len(queries)}] Benchmarking {q['id']} - {safe_title}...", end="", flush=True)
        latencies = []
        query_results = None
        
        # Run without restrictive filters (search the entire corpus)
        payload = {
            "query": q["code"],
            "top_k": 10,
            "repo_group": ["all"],
            "type_filter": ["all"],
            "language_filter": ["all"]
        }

        for r in range(runs):
            t_start = time.perf_counter()
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=5*60)
                response.raise_for_status()
                t_end = time.perf_counter()
                
                # Extract search results from the first successful run
                if query_results is None:
                    try:
                        resp_data = response.json()
                        query_results = resp_data.get("results", [])
                    except Exception as json_err:
                        print(f"\nWarning: could not parse search results for {q['id']}: {json_err}")
                
                # Latency in milliseconds
                latency_ms = (t_end - t_start) * 1000.0
                latencies.append(latency_ms)
            except Exception as e:
                print(f"\nError on query {q['id']} run {r+1}: {e}")
                # Don't fail the whole benchmark, just record None or skip
                
            # Short sleep to prevent rate limiter throttling
            time.sleep(0.05)

        if latencies:
            results[q["id"]] = {
                "title": q["title"],
                "latencies": latencies,
                "min": min(latencies),
                "max": max(latencies),
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "stddev": statistics.stdev(latencies) if len(latencies) > 1 else 0.0
            }
            print(" Done.")
        else:
            print(" Failed completely.")

        # Build evaluation record for this query
        formatted_results = []
        if query_results:
            for rank, res in enumerate(query_results, 1):
                formatted_results.append({
                    "rank": rank,
                    "name": res.get("name"),
                    "type": res.get("type"),
                    "filepath": res.get("filepath"),
                    "repo_name": res.get("repo_name"),
                    "repo_group": res.get("repo_group"),
                    "swhid": res.get("swhid"),
                    "recall_score": res.get("recall_score"),
                    "code": res.get("code")
                })
        
        evaluation_records.append({
            "id": q["id"],
            "category": q.get("category"),
            "title": q["title"],
            "language": q.get("language"),
            "code": q["code"],
            "results": formatted_results
        })

    if save_results_path and evaluation_records:
        output_data = {
            "benchmark_url": url,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "queries": evaluation_records
        }
        try:
            with open(save_results_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"Top 10 results saved to {save_results_path}")
        except Exception as save_err:
            print(f"Error saving results to {save_results_path}: {save_err}")

    return results

def print_summary_table(results):
    """Print a clean ASCII table summarizing latency results."""
    print("\n" + "=" * 80)
    print(" LATENCY BENCHMARK RESULTS (in milliseconds)")
    print("=" * 80)
    print(f"{'QID':<6} | {'Query Title':<30} | {'Min':<8} | {'Max':<8} | {'Mean':<8} | {'Median':<8} | {'StdDev':<8}")
    print("-" * 80)
    
    all_means = []
    all_medians = []
    
    # Sort results by QID category and number (e.g. A1, A2, ..., B1, B2)
    def qid_sort_key(item):
        qid = item[0]
        match = re.match(r'^([A-Z])(\d+)', qid)
        if match:
            return (match.group(1), int(match.group(2)))
        return (qid, 0)

    for qid, stats in sorted(results.items(), key=qid_sort_key):
        title = stats["title"]
        if len(title) > 30:
            title = title[:27] + "..."
        print(f"{qid:<6} | {title:<30} | {stats['min']:8.1f} | {stats['max']:8.1f} | {stats['mean']:8.1f} | {stats['median']:8.1f} | {stats['stddev']:8.1f}")
        all_means.append(stats["mean"])
        all_medians.append(stats["median"])

    print("-" * 80)
    if all_means:
        print(f"{'OVERALL AVERAGE':<38} | {'':<8} | {'':<8} | {statistics.mean(all_means):8.1f} | {statistics.median(all_medians):8.1f} |")
    print("=" * 80)

def generate_boxplot(results, plot_path):
    """Generate a horizontal box-and-whisker plot for latencies."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not found. Skipping plot generation.")
        return

    print(f"Generating boxplot at: {plot_path}...")
    
    # Sort queries by median latency (ascending) for better visualization
    sorted_items = sorted(results.items(), key=lambda x: x[1]["median"])
    
    labels = [f"{item[0]} - {item[1]['title'][:25]}..." if len(item[1]['title']) > 25 else f"{item[0]} - {item[1]['title']}" 
              for item in sorted_items]
    data = [item[1]["latencies"] for item in sorted_items]

    # Create figure with high quality DPI and custom size
    plt.figure(figsize=(10, 8), dpi=150)
    
    # Customize boxplot design (branding color #3366cc)
    boxplot_kwargs = dict(
        vert=False,
        patch_artist=True,
        showmeans=True,
        meanline=True,
        boxprops=dict(facecolor="#eaf3ff", color="#3366cc", linewidth=1.5),
        medianprops=dict(color="#3366cc", linewidth=2.0),
        whiskerprops=dict(color="#a2a9b1", linewidth=1.2),
        capprops=dict(color="#a2a9b1", linewidth=1.2),
        meanprops=dict(color="#2a55a3", linestyle="--", linewidth=1.2),
        flierprops=dict(marker="o", markerfacecolor="#fee7e6", markeredgecolor="#b32424", markersize=5)
    )

    try:
        box = plt.boxplot(data, tick_labels=labels, **boxplot_kwargs)
    except TypeError:
        box = plt.boxplot(data, labels=labels, **boxplot_kwargs)

    # Labels and Titles
    plt.title("API Latency Distribution per Evaluation Query", fontsize=14, fontweight="bold", pad=15, color="#202122")
    plt.xlabel("Latency (milliseconds)", fontsize=11, labelpad=10, color="#202122")
    plt.ylabel("Evaluation Queries", fontsize=11, labelpad=10, color="#202122")
    
    # Grid lines
    plt.grid(axis="x", linestyle=":", alpha=0.6, color="#a2a9b1")
    
    # Style tick labels
    plt.tick_params(colors="#54595d")
    
    # Ensure layout fits labels
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    print("Boxplot successfully saved.")

def main():
    parser = argparse.ArgumentParser(description="MediaWiki Code2Code Search Latency Benchmark")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Target API search endpoint (default: {DEFAULT_URL})")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help=f"Number of repetitions per query (default: {DEFAULT_RUNS})")
    parser.add_argument("--plot", default=DEFAULT_PLOT_PATH, help=f"Output file path for the boxplot chart (default: {DEFAULT_PLOT_PATH})")
    parser.add_argument("--queries-json", default=None, help="Path to evaluation queries JSON file")
    parser.add_argument("--tex-path", default=None, help="Path to evaluation queries LaTeX file")
    parser.add_argument("--save-results", default=None, help="Path to save evaluation results JSON")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))

    # Determine paths
    tex_path = args.tex_path or os.path.join(project_root, "manuscript", "evaluation_queries.tex")
    queries_json_path = args.queries_json or os.path.join(script_dir, "evaluation_queries.json")
    save_results_path = args.save_results or os.path.join(script_dir, "evaluation_results.json")

    # Load or parse queries
    queries = []
    if os.path.exists(queries_json_path):
        print(f"Loading queries from JSON: {queries_json_path}")
        try:
            with open(queries_json_path, "r", encoding="utf-8") as f:
                queries = json.load(f)
            # Force regeneration if language is null (old parser format)
            if queries and all(q.get("language") is None for q in queries):
                print("Old format detected in queries JSON. Forcing regeneration...")
                queries = []
        except Exception as e:
            print(f"Error loading JSON queries: {e}. Falling back to parsing LaTeX...")
            
    if not queries:
        print(f"Extracting queries from LaTeX: {tex_path}")
        queries = parse_queries(tex_path)
        if queries:
            print(f"Saving preprocessed queries to: {queries_json_path}")
            try:
                save_queries_to_json(queries, queries_json_path)
            except Exception as e:
                print(f"Error saving preprocessed queries to JSON: {e}")

    if not queries:
        print("Error: No queries loaded or extracted.")
        sys.exit(1)

    # Run the benchmark
    results = run_benchmark(queries, args.url, args.runs, save_results_path)
    
    if not results:
        print("Error: No benchmark results collected.")
        sys.exit(1)

    # Print summary and save plot
    print_summary_table(results)
    generate_boxplot(results, args.plot)

if __name__ == "__main__":
    main()
