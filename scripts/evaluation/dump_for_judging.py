"""Dump pooled top-10 results (BM25 + Code2Code) per query into readable
worksheets for manual P@10 judging. One file per category."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "evaluation_results_code2codesearch_toolforge_org_search_7runs.json"), encoding="utf-8") as f:
    neural = json.load(f)["queries"]
with open(os.path.join(HERE, "bm25_results_code2codesearch_toolforge_org_search_7runs.json"), encoding="utf-8") as f:
    bm25 = json.load(f)["queries"]

neural_by_id = {q["id"]: q for q in neural}
bm25_by_id = {q["id"]: q for q in bm25}

MAXLINES = 35


def trunc(code):
    lines = (code or "").split("\n")
    if len(lines) > MAXLINES:
        lines = lines[:MAXLINES] + [f"... [+{len(lines) - MAXLINES} more lines]"]
    return "\n".join(lines)


def render_results(results):
    out = []
    for r in results:
        out.append(f"  --- rank {r['rank']} | {r['type']} | name: {r['name']}")
        out.append(f"      repo: {r['repo_name']} ({r.get('repo_group','')}) | file: {r['filepath']}")
        out.append(f"      score: {r['recall_score']:.4f}")
        out.append("      CODE:")
        for ln in trunc(r["code"]).split("\n"):
            out.append(f"        {ln}")
        out.append("")
    return "\n".join(out)


categories = {}
for q in neural:
    categories.setdefault(q["category"], []).append(q["id"])

for cat, ids in sorted(categories.items()):
    path = os.path.join(HERE, f"judging_cat_{cat}.txt")
    with open(path, "w", encoding="utf-8") as f:
        for qid in ids:
            nq = neural_by_id[qid]
            bq = bm25_by_id.get(qid, {"results": []})
            f.write("=" * 90 + "\n")
            f.write(f"QUERY {qid} [{nq['category']}] {nq['title']} (lang: {nq['language']})\n")
            f.write("=" * 90 + "\n")
            f.write("QUERY CODE:\n")
            for ln in (nq["code"] or "").split("\n"):
                f.write(f"    {ln}\n")
            f.write("\n")
            f.write("-" * 90 + "\n")
            f.write(f"### BM25 top-10 for {qid}\n")
            f.write("-" * 90 + "\n")
            f.write(render_results(bq["results"]))
            f.write("\n")
            f.write("-" * 90 + "\n")
            f.write(f"### CODE2CODE (neural) top-10 for {qid}\n")
            f.write("-" * 90 + "\n")
            f.write(render_results(nq["results"]))
            f.write("\n\n")
    print(f"Wrote {path}")
