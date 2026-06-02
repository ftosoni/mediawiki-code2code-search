import os
import re
import sys
import time
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

def main():
    parser = argparse.ArgumentParser(description="Build BM25 Search Index and Cache it")
    parser.add_argument("--db-path", default=None, help="Path to SQLite database")
    parser.add_argument("--index-path", default=None, help="Path to serialize BM25 index pickle file")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))

    # Determine paths
    db_path = args.db_path or os.path.join(project_root, "backend", "functions.db")
    index_path = args.index_path or os.path.join(project_root, "backend", "bm25_index.pkl")

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        sys.exit(1)

    print(f"Loading corpus from SQLite at {db_path}...")
    t0 = time.time()
    conn = sqlite3.connect(db_path)
    # We select 'code' since that's the column containing the source code
    rows = conn.execute("SELECT id, code FROM functions").fetchall()
    conn.close()
    print(f"Loaded {len(rows)} functions in {time.time() - t0:.2f}s")

    print("Tokenizing corpus...")
    t0 = time.time()
    ids = [r[0] for r in rows]
    corpus = [tokenize_code(r[1] or "") for r in rows]
    print(f"Tokenized corpus in {time.time() - t0:.2f}s")

    print("Building BM25 index...")
    t0 = time.time()
    bm25 = BM25Okapi(corpus)
    print(f"Built BM25 index in {time.time() - t0:.2f}s")

    print(f"Saving serialized BM25 index to {index_path}...")
    t0 = time.time()
    try:
        with open(index_path, "wb") as f:
            pickle.dump({"bm25": bm25, "ids": ids}, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"Saved index in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"Error saving BM25 index to cache: {e}")
        sys.exit(1)
        
    print("BM25 index successfully built and saved.")

if __name__ == "__main__":
    main()
