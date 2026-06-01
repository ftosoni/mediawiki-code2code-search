import os
import re
import sys
import time
import argparse
import statistics
import requests

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
    in_listing = False
    current_code = []

    def clean_title(title_text):
        # Remove LaTeX macros like \qlang, \texttt, and clean spaces
        title_text = re.sub(r'\\qlang\{.*?\}', '', title_text)
        title_text = re.sub(r'\\texttt\{([^}]+)\}', r'\1', title_text)
        title_text = re.sub(r'[\s~]+', ' ', title_text)
        # Normalize double dashes or long dashes
        title_text = title_text.replace("—", "-").replace("–", "-")
        return title_text.strip(" - \t\n")

    for line in content.splitlines():
        if line.startswith(r"\subsection*"):
            match = re.search(r'\\subsection\*\{([^}]+)\}', line)
            if match:
                current_title = clean_title(match.group(1))
        elif r"\begin{lstlisting}" in line:
            in_listing = True
            current_code = []
        elif r"\end{lstlisting}" in line:
            in_listing = False
            if current_title and current_code:
                code_text = "\n".join(current_code)
                # Extract QID (like A1, B12, C3) from the title
                qid_match = re.match(r'^([A-Z]\d+)', current_title)
                qid = qid_match.group(1) if qid_match else "Q"
                queries.append({
                    "id": qid,
                    "title": current_title,
                    "code": code_text
                })
                current_title = None
                current_code = []
        elif in_listing:
            current_code.append(line)

    return queries

def run_benchmark(queries, url, runs):
    """Run benchmark against the target search API url."""
    print(f"Starting latency benchmark against: {url}")
    print(f"Number of queries: {len(queries)}")
    print(f"Repetitions per query: {runs}")
    print("=" * 60)

    results = {}
    
    # Pre-heat the connection
    print("Pre-heating connection...")
    try:
        requests.post(url, json={
            "query": "preheat connection",
            "top_k": 1,
            "repo_group": ["all"],
            "type_filter": ["all"],
            "language_filter": ["all"]
        }, timeout=15)
    except Exception as e:
        print(f"Warning during preheat: {e}")

    for idx, q in enumerate(queries, 1):
        print(f"[{idx}/{len(queries)}] Benchmarking {q['id']} - {q['title']}...", end="", flush=True)
        latencies = []
        
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
                response = requests.post(url, json=payload, timeout=20)
                response.raise_for_status()
                t_end = time.perf_counter()
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
    box = plt.boxplot(data, vert=False, labels=labels, patch_artist=True,
                      showmeans=True, meanline=True,
                      boxprops=dict(facecolor="#eaf3ff", color="#3366cc", linewidth=1.5),
                      medianprops=dict(color="#3366cc", linewidth=2.0),
                      whiskerprops=dict(color="#a2a9b1", linewidth=1.2),
                      capprops=dict(color="#a2a9b1", linewidth=1.2),
                      meanprops=dict(color="#2a55a3", linestyle="--", linewidth=1.2),
                      flierprops=dict(marker="o", markerfacecolor="#fee7e6", markeredgecolor="#b32424", markersize=5))

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
    args = parser.parse_args()

    # Locate evaluation_queries.tex
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    tex_path = os.path.join(project_root, "manuscript", "evaluation_queries.tex")

    print("Extracting queries from LaTeX...")
    queries = parse_queries(tex_path)
    
    if not queries:
        print("Error: No queries extracted. Please check the LaTeX file format.")
        sys.exit(1)

    # Run the benchmark
    results = run_benchmark(queries, args.url, args.runs)
    
    if not results:
        print("Error: No benchmark results collected.")
        sys.exit(1)

    # Print summary and save plot
    print_summary_table(results)
    generate_boxplot(results, args.plot)

if __name__ == "__main__":
    main()
