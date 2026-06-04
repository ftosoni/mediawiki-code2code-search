"""Quantify near-duplicate density in the top-10 result lists of each system,
to support an honest remark in the manuscript. A 'duplicate' is defined
conservatively as a byte-identical code snippet within the same top-10 list."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(fn):
    with open(os.path.join(HERE, fn), encoding="utf-8") as f:
        return json.load(f)["queries"]


def stats(queries, label):
    n = len(queries)
    distinct_code, distinct_name = [], []
    repo_collisions = 0  # lists where the same code appears in >=2 repos
    worst = None
    for q in queries:
        codes = [r["code"] for r in q["results"]]
        names = [r["name"] for r in q["results"]]
        dc = len(set(codes))
        distinct_code.append(dc)
        distinct_name.append(len(set(names)))
        # max multiplicity of any single code in this list
        mult = max(codes.count(c) for c in set(codes))
        if mult >= 2:
            repo_collisions += 1
        if worst is None or mult > worst[1]:
            worst = (q["id"], mult)
    print(f"== {label} (n={n}) ==")
    print(f"  mean distinct snippets / top-10 (by exact code): {sum(distinct_code)/n:.2f}")
    print(f"  mean distinct snippets / top-10 (by name):       {sum(distinct_name)/n:.2f}")
    print(f"  lists containing >=1 exact-duplicate snippet:    {repo_collisions}/{n}")
    print(f"  worst single-snippet multiplicity:               {worst[1]} (query {worst[0]})")
    return sum(distinct_code) / n


neural = load("evaluation_results.json")
bm25 = load("bm25_results.json")
c = stats(neural, "Code2Code")
b = stats(bm25, "BM25")
