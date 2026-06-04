"""Quantify near-duplicate density in the top-10 result lists of each system,
to support an honest remark in the manuscript. A 'duplicate' is defined
conservatively as a byte-identical code snippet within the same top-10 list.

For each system (BM25, Code2Code) over the 27 benchmark queries the script
reports:
  - mean number of distinct snippets per top-10 (by exact code and by name);
  - how many queries contain >=1 duplicate;
  - the total number of duplicate (redundant) entries;
  - the mean number of duplicates per query, both over all 27 queries and
    over only the lists that actually contain a duplicate;
  - the maximum number of duplicates in a single list;
  - the worst single-snippet multiplicity (most copies of one snippet)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(fn):
    with open(os.path.join(HERE, fn), encoding="utf-8") as f:
        return json.load(f)["queries"]


def stats(queries, label):
    n = len(queries)
    distinct_code, distinct_name = [], []
    dups = []            # redundant entries per list = (#results - #distinct codes)
    repo_collisions = 0  # lists where the same code appears in >=2 repos
    worst = None         # (qid, max multiplicity of any single snippet)
    worst_dups = None    # (qid, max redundant entries in a single list)
    for q in queries:
        codes = [r["code"] for r in q["results"]]
        names = [r["name"] for r in q["results"]]
        k = len(codes)
        dc = len(set(codes))
        distinct_code.append(dc)
        distinct_name.append(len(set(names)))
        # redundant (byte-identical duplicate) entries in this list
        d = k - dc
        dups.append(d)
        # max multiplicity of any single code in this list
        mult = max(codes.count(c) for c in set(codes))
        if mult >= 2:
            repo_collisions += 1
        if worst is None or mult > worst[1]:
            worst = (q["id"], mult)
        if worst_dups is None or d > worst_dups[1]:
            worst_dups = (q["id"], d)
    with_dup = [d for d in dups if d > 0]
    mean_all = sum(dups) / n
    mean_wd = sum(with_dup) / len(with_dup) if with_dup else 0.0

    def row(label_, value):
        print(f"  {label_:<49}{value}")

    print(f"== {label} (n={n}) ==")
    row("mean distinct snippets / top-10 (by exact code):", f"{sum(distinct_code)/n:.2f}")
    row("mean distinct snippets / top-10 (by name):", f"{sum(distinct_name)/n:.2f}")
    row("lists containing >=1 exact-duplicate snippet:", f"{repo_collisions}/{n}")
    row("total duplicate (redundant) entries:", f"{sum(dups)}")
    row(f"mean duplicates / query (over all {n}):", f"{mean_all:.2f}")
    row(f"mean duplicates / query (lists w/ dup, {len(with_dup)}):", f"{mean_wd:.2f}")
    row("max duplicates in a single list:", f"{worst_dups[1]} (query {worst_dups[0]})")
    row("worst single-snippet multiplicity:", f"{worst[1]} (query {worst[0]})")
    return {
        "n": n,
        "mean_distinct_code": sum(distinct_code) / n,
        "mean_distinct_name": sum(distinct_name) / n,
        "lists_with_duplicate": repo_collisions,
        "total_duplicates": sum(dups),
        "mean_duplicates_all": mean_all,
        "mean_duplicates_with_dup": mean_wd,
        "max_duplicates_single_list": worst_dups,
        "worst_single_snippet_multiplicity": worst,
    }


neural = load("evaluation_results_code2codesearch_toolforge_org_search_7runs.json")
bm25 = load("bm25_results_code2codesearch_toolforge_org_search_7runs.json")
c = stats(neural, "Code2Code")
b = stats(bm25, "BM25")
