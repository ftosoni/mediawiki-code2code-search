import os
import re
import sys
import time
import json
import pickle
import sqlite3
import argparse
from rank_bm25 import BM25Okapi

def tokenize_code(code: str) -> list[str]:
    # split on non-word characters, filter short tokens and keyword noise
    tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+', code)
    STOP = {'return', 'function', 'def', 'if', 'else', 'for',
            'while', 'true', 'false', 'null', 'None', 'int',
            'str', 'bool', 'var', 'let', 'const', 'new', 'this'}
    return [t for t in tokens if t not in STOP and len(t) > 2]

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

def main():
    parser = argparse.ArgumentParser(description="BM25 Search Baseline Evaluation")
    parser.add_argument("--url", default="https://code2codesearch.toolforge.org/search", help="Target API search endpoint for filename alignment")
    parser.add_argument("--runs", type=int, default=7, help="Number of repetitions for filename alignment")
    parser.add_argument("--queries-json", default=None, help="Path to evaluation queries JSON file")
    parser.add_argument("--tex-path", default=None, help="Path to evaluation queries LaTeX file")
    parser.add_argument("--save-results", default=None, help="Path to save BM25 evaluation results JSON")
    parser.add_argument("--db-path", default=None, help="Path to SQLite database")
    parser.add_argument("--index-path", default=None, help="Path to serialized BM25 index pickle file")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))

    # Sanitize URL for filename
    url_part = re.sub(r'^https?://', '', args.url)
    url_part = re.sub(r'[^a-zA-Z0-9]', '_', url_part)
    url_part = re.sub(r'_+', '_', url_part).strip('_')
    suffix = f"{url_part}_{args.runs}runs"

    # Determine paths
    db_path = args.db_path or os.path.join(project_root, "backend", "snippets.db")
    tex_path = args.tex_path or os.path.join(project_root, "manuscript", "evaluation_queries.tex")
    queries_json_path = args.queries_json or os.path.join(script_dir, "evaluation_queries.json")
    save_results_path = args.save_results or os.path.join(script_dir, f"bm25_results_{suffix}.json")
    index_path = args.index_path or os.path.join(project_root, "backend", "bm25_index.pkl")

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

    # Load BM25 index & IDs
    bm25 = None
    ids = []
    
    if os.path.exists(index_path):
        print(f"Loading cached BM25 index from {index_path}...")
        t0 = time.time()
        try:
            with open(index_path, "rb") as f:
                data = pickle.load(f)
                bm25 = data["bm25"]
                ids = data["ids"]
            print(f"Loaded index in {time.time() - t0:.2f}s")
        except Exception as e:
            print(f"Error loading index: {e}")
            sys.exit(1)
    else:
        print(f"Error: BM25 index pickle file not found at {index_path}.")
        print("Please run scripts/evaluation/build_bm25_index.py first to build the index.")
        sys.exit(1)

    # Run search for each query
    evaluation_records = []
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    print("Running evaluation queries against BM25...")
    for idx, q in enumerate(queries, 1):
        # Safe title printing for Windows consoles
        safe_title = q['title'].encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
        print(f"[{idx}/{len(queries)}] Searching BM25 for {q['id']} - {safe_title}...")
        q_tokens = tokenize_code(q["code"])
        scores = bm25.get_scores(q_tokens)
        
        # Get top 10 indices
        top10_idx = scores.argsort()[::-1][:10]
        
        # Map back to SQLite row IDs and save scores
        top10_results = []
        for rank_idx, i in enumerate(top10_idx, 1):
            doc_id = ids[i]
            score = float(scores[i])
            
            # Fetch metadata from SQLite
            row = conn.execute("SELECT * FROM snippets WHERE id = ?", (doc_id,)).fetchone()
            if row:
                top10_results.append({
                    "rank": rank_idx,
                    "name": row["name"],
                    "type": row["type"],
                    "filepath": row["filepath"],
                    "repo_name": row["repo_name"],
                    "repo_group": row["repo_group"],
                    "swhid": row["swhid"],
                    "recall_score": score,
                    "code": row["code"]
                })
        
        evaluation_records.append({
            "id": q["id"],
            "category": q.get("category"),
            "title": q["title"],
            "language": q.get("language"),
            "code": q["code"],
            "results": top10_results
        })

    conn.close()

    # Save BM25 results
    output_data = {
        "benchmark_url": "BM25 Baseline",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "queries": evaluation_records
    }
    try:
        with open(save_results_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"BM25 baseline results saved to {save_results_path}")
    except Exception as save_err:
        print(f"Error saving BM25 results: {save_err}")

if __name__ == "__main__":
    main()
