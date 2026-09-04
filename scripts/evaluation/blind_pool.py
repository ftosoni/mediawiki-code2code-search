"""Blinded pooling + randomization for the LLM-as-a-judge evaluation.

For each benchmark query we

  1. pool the top-10 results of both retrieval systems (BM25 baseline +
     Code2Code semantic retriever),
  2. deduplicate byte-identical snippets across systems by a content hash, so a
     snippet returned by both systems gets ONE doc_id and ONE label,
  3. shuffle the pool with a per-query reproducible seed, and
  4. render a self-contained judge prompt containing NO system identity, no
     filenames, no ranks and no scores -- only anonymous ``doc_id``s.

The judge sees one shuffled pool per query, never the two ranked lists.

Outputs (under ``--out-dir``, default ``judging/``):

  judge_inputs/prompt_<QID>.md   one blinded prompt per query (send to each judge)
  pool_provenance.json           the answer key -- doc_id -> content hash,
                                 hash -> {"bm25": rank|None, "c2c": rank|None},
                                 the pooled doc text, and the run parameters.
                                 NEVER shown to the judge.
  gold_sheet.md / gold_template.json   (only with --gold-sample N) a random
                                 cross-query sample of pooled docs with blank
                                 score fields, for human agreement labelling.

Original ranks and system identity live ONLY in pool_provenance.json and are
re-joined to the judge's labels by analyze_labels.py, after grading, in code --
never in the model.

Usage
-----
    python blind_pool.py                     # shuffled pools, default seed
    python blind_pool.py --seed 20260824
    python blind_pool.py --order c2c         # bias sanity check (unshuffled)
    python blind_pool.py --gold-sample 80    # also emit a human gold sheet
"""
import argparse
import hashlib
import json
import os
import random
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

# The two systems, mapped to the result files they were dumped from. The keys
# ("bm25", "c2c") are the internal system identifiers used throughout the
# harness; they never appear in a prompt.
DEFAULT_SOURCES = {
    "bm25": "bm25_results_code2codesearch_toolforge_org_search_7runs.json",
    "c2c": "evaluation_results_127_0_0_1_8000_search_7runs.json",
}

DEFAULT_SEED = 20260824
TEMPLATE_NAME = "judge_prompt_template.md"


def normalize(snippet: str) -> str:
    """Collapse all runs of whitespace so trivially-different copies of the same
    snippet (indentation, trailing newlines, CRLF vs LF) dedup together."""
    return " ".join((snippet or "").split())


def content_hash(snippet: str) -> str:
    return hashlib.sha256(normalize(snippet).encode("utf-8")).hexdigest()[:16]


def build_pool(query_id, results_by_system, seed, order="shuffle"):
    """Pool, dedup and order the candidates for one query.

    Returns ``(prompt_docs, id_to_hash, provenance)`` where

      prompt_docs  list of {"doc_id", "code"} in presentation order
      id_to_hash   doc_id -> content hash
      provenance   content hash -> {"bm25": rank|None, "c2c": rank|None}

    ``provenance`` never enters the prompt.
    """
    pool = {}         # content_hash -> doc text (first seen wins)
    provenance = {}   # content_hash -> {"bm25": rank|None, "c2c": rank|None}
    systems = list(results_by_system)

    for system in systems:
        for rank, r in enumerate(results_by_system[system], start=1):
            h = content_hash(r["code"])
            pool.setdefault(h, r["code"])
            provenance.setdefault(h, {s: None for s in systems})
            # keep the best (lowest) rank if a system returns a duplicate
            if provenance[h][system] is None:
                provenance[h][system] = rank

    hashes = list(pool)
    if order == "shuffle":
        rng = random.Random(f"{seed}:{query_id}")   # per-query, reproducible
        rng.shuffle(hashes)
    elif order == "c2c":
        # Sanity check for residual presentation bias: order by C2C rank, with
        # C2C-absent docs (BM25-only) appended by BM25 rank. Deterministic.
        hashes.sort(key=lambda h: (
            provenance[h]["c2c"] is None,
            provenance[h]["c2c"] if provenance[h]["c2c"] is not None else 0,
            provenance[h]["bm25"] if provenance[h]["bm25"] is not None else 999,
        ))
    else:
        raise ValueError(f"unknown order: {order!r}")

    prompt_docs = [
        {"doc_id": f"d{i:03d}", "code": pool[h]}
        for i, h in enumerate(hashes, start=1)
    ]
    id_to_hash = {f"d{i:03d}": h for i, h in enumerate(hashes, start=1)}
    return prompt_docs, id_to_hash, provenance


def safe_fence(code: str) -> str:
    """Return a backtick fence strictly longer than the longest backtick run in
    ``code`` so a snippet containing ``` cannot break out of its block."""
    longest = 0
    run = 0
    for ch in code or "":
        run = run + 1 if ch == "`" else 0
        longest = max(longest, run)
    return "`" * max(3, longest + 1)


def render_candidates(prompt_docs) -> str:
    blocks = []
    for d in prompt_docs:
        fence = safe_fence(d["code"])
        blocks.append(f"### {d['doc_id']}\n{fence}\n{d['code']}\n{fence}")
    return "\n\n".join(blocks)


def render_prompt(template, query_id, query_code, prompt_docs) -> str:
    # Substitute the query block and candidate list first, then the id, so that
    # nothing inside the (untrusted) code can collide with a later placeholder.
    out = template.replace("{QUERY_CODE}", query_code or "")
    out = out.replace("{CANDIDATES}", render_candidates(prompt_docs))
    out = out.replace("{QUERY_ID}", query_id)
    return out


def load_queries(sources):
    """Load each source file and index its queries by id. Returns
    ``(by_system, query_meta)`` where by_system[system][qid] = results list and
    query_meta[qid] = {"code", "title", "category", "language"}."""
    by_system = {}
    query_meta = {}
    for system, fname in sources.items():
        with open(os.path.join(HERE, fname), encoding="utf-8") as f:
            queries = json.load(f)["queries"]
        by_system[system] = {}
        for q in queries:
            by_system[system][q["id"]] = q["results"]
            # Prefer the query code/metadata from the first source that has it;
            # the query snippet is identical across systems.
            query_meta.setdefault(q["id"], {
                "code": q.get("code", ""),
                "title": q.get("title", ""),
                "category": q.get("category", ""),
                "language": q.get("language", ""),
            })
    return by_system, query_meta


def sample_gold(provenance_all, docs_all, n, seed):
    """Draw a reproducible cross-query sample of (query_id, doc_id) pairs for
    human agreement labelling. Returns a list of sample records."""
    flat = []
    for qid in sorted(provenance_all):
        for doc_id in sorted(docs_all[qid]):
            flat.append((qid, doc_id))
    rng = random.Random(f"{seed}:gold")
    rng.shuffle(flat)
    return flat[: min(n, len(flat))]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED,
                    help=f"master seed for per-query shuffling (default {DEFAULT_SEED})")
    ap.add_argument("--order", choices=["shuffle", "c2c"], default="shuffle",
                    help="'shuffle' (blinded, default) or 'c2c' (unshuffled bias check)")
    ap.add_argument("--out-dir", default=os.path.join(HERE, "judging"),
                    help="output directory (default: ./judging)")
    ap.add_argument("--gold-sample", type=int, default=0, metavar="N",
                    help="also emit a human gold sheet sampling N pooled docs")
    ap.add_argument("--sources", nargs="+", metavar="SYSTEM=FILE",
                    help="override default result files, e.g. c2c=foo.json")
    args = ap.parse_args()

    sources = dict(DEFAULT_SOURCES)
    for spec in args.sources or []:
        system, _, fname = spec.partition("=")
        sources[system] = fname

    with open(os.path.join(HERE, TEMPLATE_NAME), encoding="utf-8") as f:
        template = f.read()

    by_system, query_meta = load_queries(sources)
    query_ids = sorted(query_meta, key=lambda q: (q[0], int(q[1:])) if q[1:].isdigit() else (q, 0))

    inputs_dir = os.path.join(args.out_dir, "judge_inputs")
    os.makedirs(inputs_dir, exist_ok=True)

    provenance_all = {}   # qid -> {hash -> ranks}
    id_to_hash_all = {}   # qid -> {doc_id -> hash}
    docs_all = {}         # qid -> {doc_id -> code}

    for qid in query_ids:
        results_by_system = {s: by_system[s].get(qid, []) for s in sources}
        prompt_docs, id_to_hash, provenance = build_pool(
            qid, results_by_system, args.seed, order=args.order)

        prompt = render_prompt(template, qid, query_meta[qid]["code"], prompt_docs)
        with open(os.path.join(inputs_dir, f"prompt_{qid}.md"), "w", encoding="utf-8") as f:
            f.write(prompt)

        provenance_all[qid] = provenance
        id_to_hash_all[qid] = id_to_hash
        docs_all[qid] = {d["doc_id"]: d["code"] for d in prompt_docs}

    prompt_hash = hashlib.sha256(template.encode("utf-8")).hexdigest()[:16]
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "order": args.order,
        "systems": list(sources),
        "sources": sources,
        "prompt_template": TEMPLATE_NAME,
        "prompt_hash": prompt_hash,
        "n_queries": len(query_ids),
        "query_meta": query_meta,
        "per_query": {
            qid: {
                "id_to_hash": id_to_hash_all[qid],
                "provenance": provenance_all[qid],
                "docs": docs_all[qid],
                "pool_size": len(id_to_hash_all[qid]),
            }
            for qid in query_ids
        },
    }
    prov_path = os.path.join(args.out_dir, "pool_provenance.json")
    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    total_docs = sum(len(id_to_hash_all[q]) for q in query_ids)
    total_dupes = sum(
        1 for q in query_ids for h, p in provenance_all[q].items()
        if all(p[s] is not None for s in sources)
    )
    print(f"Wrote {len(query_ids)} blinded prompts to {inputs_dir}")
    print(f"Pooled {total_docs} unique docs; {total_dupes} shared by all systems (single label).")
    print(f"Provenance (answer key): {prov_path}")
    print(f"seed={args.seed} order={args.order} prompt_hash={prompt_hash}")

    if args.gold_sample > 0:
        sample = sample_gold(provenance_all, docs_all, args.gold_sample, args.seed)
        gold_template = {
            "instructions": (
                "Fill in each 'score' with 1.0 / 0.5 / 0.0 / null following the "
                "same rubric as the judges. Do not edit query_id/doc_id. Save as "
                "human_gold.json and pass to analyze_labels.py --human-gold."
            ),
            "seed": args.seed,
            "labels": {
                f"{qid}:{doc_id}": {"query_id": qid, "doc_id": doc_id, "score": None}
                for qid, doc_id in sample
            },
        }
        with open(os.path.join(args.out_dir, "gold_template.json"), "w", encoding="utf-8") as f:
            json.dump(gold_template, f, indent=2, ensure_ascii=False)
        with open(os.path.join(args.out_dir, "gold_sheet.md"), "w", encoding="utf-8") as f:
            f.write(f"# Human gold labelling sheet ({len(sample)} pooled docs)\n\n")
            f.write("Score each snippet 1.0 / 0.5 / 0.0 / null, then transcribe the "
                    "scores into gold_template.json.\n\n")
            for qid, doc_id in sample:
                code = docs_all[qid][doc_id]
                fence = safe_fence(code)
                f.write(f"## {qid}:{doc_id}  — score: ____\n\n")
                f.write("Query:\n")
                qfence = safe_fence(query_meta[qid]["code"])
                f.write(f"{qfence}\n{query_meta[qid]['code']}\n{qfence}\n\n")
                f.write("Candidate:\n")
                f.write(f"{fence}\n{code}\n{fence}\n\n---\n\n")
        print(f"Wrote gold sheet ({len(sample)} docs) and gold_template.json to {args.out_dir}")


if __name__ == "__main__":
    main()
