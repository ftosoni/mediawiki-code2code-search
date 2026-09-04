"""Metrics + agreement analysis for the blinded LLM-as-a-judge evaluation.

Reads the blinding answer key (``pool_provenance.json``, produced by
``blind_pool.py``) and one label file per (judge, repeat), re-joins the judge's
anonymous ``doc_id`` labels to the hidden system provenance, and computes the
retrieval metrics in code -- never in the model.

What it computes
----------------
* Median label per document across repeats (per spec) and per-document label
  variance -- high-variance docs are the ambiguous cases for the error analysis.
* P@10 lenient (median score >= 0.5) and strict (== 1.0), per system per judge.
* nDCG@10 (rank-aware) per system per judge.
* Bootstrap 95% CIs over queries, for each system and for the paired C2C-BM25
  delta -- reported per judge, plus the jury (across-judge) mean.
* Cohen's kappa of each judge against the human gold labels (if provided).
* Krippendorff's alpha across judges over the full pooled label set.

Nothing here reveals system identity to any model; the qualitative second pass
(which does) is run separately, only after these numbers are frozen.

Label file format (one per judge x repeat), e.g. judge_outputs/<judge>__rep1.json::

    {
      "judge": "claude-opus-4-8-20260601",   # dated id, never a -latest alias
      "repeat": 1,
      "temperature": 0.0,
      "seed": 20260824,
      "prompt_hash": "....",
      "labels": {
        "A1": {"d001": {"score": 1.0, "rationale": "..."}, ...},
        "A2": {...}
      }
    }

Usage
-----
    python analyze_labels.py
    python analyze_labels.py --judging-dir judging --outputs judging/judge_outputs
    python analyze_labels.py --human-gold judging/human_gold.json
"""
import argparse
import glob
import json
import math
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CATEGORIES = [0.0, 0.5, 1.0]      # the graded relevance classes (null excluded)
LENIENT = 0.5
STRICT = 1.0
BOOTSTRAP_N = 10000
BOOTSTRAP_SEED = 20260824


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_provenance(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_label_files(paths):
    """Return {judge_id: {repeat: {qid: {doc_id: score|None}}}}."""
    judges = defaultdict(lambda: defaultdict(dict))
    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        judge = data.get("judge") or os.path.splitext(os.path.basename(path))[0]
        repeat = data.get("repeat", 0)
        for qid, doc_labels in data["labels"].items():
            judges[judge][repeat][qid] = {
                doc_id: _coerce_score(v.get("score") if isinstance(v, dict) else v)
                for doc_id, v in doc_labels.items()
            }
    return judges


def _coerce_score(s):
    if s is None:
        return None
    s = float(s)
    if s not in CATEGORIES:
        # snap to nearest legal grade so a stray 0.75 does not poison metrics
        s = min(CATEGORIES, key=lambda c: abs(c - s))
    return s


# --------------------------------------------------------------------------- #
# Aggregation across repeats
# --------------------------------------------------------------------------- #
def median(values):
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    n = len(vals)
    mid = n // 2
    return vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2


def pvariance(values):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    return sum((v - mean) ** 2 for v in vals) / len(vals)


def collapse_repeats(judge_repeats):
    """{repeat: {qid: {doc: score}}} -> (median_labels, variances) both
    {qid: {doc: value}}."""
    per_doc = defaultdict(lambda: defaultdict(list))
    for repeat, per_query in judge_repeats.items():
        for qid, docs in per_query.items():
            for doc_id, score in docs.items():
                per_doc[qid][doc_id].append(score)
    medians = {qid: {d: median(v) for d, v in docs.items()} for qid, docs in per_doc.items()}
    variances = {qid: {d: pvariance(v) for d, v in docs.items()} for qid, docs in per_doc.items()}
    return medians, variances


def labels_by_hash(median_labels_q, id_to_hash):
    """Map a query's {doc_id: score} to {hash: score} using the answer key."""
    return {id_to_hash[d]: s for d, s in median_labels_q.items() if d in id_to_hash}


# --------------------------------------------------------------------------- #
# Metrics (computed in code, per the spec)
# --------------------------------------------------------------------------- #
def p_at_k(labels, provenance, system, k, threshold=LENIENT):
    """Fraction of a system's top-k whose (median) label meets ``threshold``.

    ``labels`` is keyed by content hash; ``provenance`` maps hash ->
    {system: rank|None}. Divided by k (fixed cut-off), so a short list is
    penalised for the missing positions, as intended for P@k.
    """
    hits = [
        labels.get(h) for h, p in provenance.items()
        if p.get(system) is not None and p[system] <= k
    ]
    return sum(1 for s in hits if s is not None and s >= threshold) / k


def p_at_10(labels, provenance, system, threshold=LENIENT):
    return p_at_k(labels, provenance, system, 10, threshold)


def mrr(labels, provenance, system, threshold=LENIENT):
    """Reciprocal rank of the first result meeting ``threshold`` (0 if none)."""
    ranked = sorted(
        (p[system], labels.get(h)) for h, p in provenance.items()
        if p.get(system) is not None
    )
    for rank, gain in ranked:
        if gain is not None and gain >= threshold:
            return 1.0 / rank
    return 0.0


def ndcg_at_10(labels, provenance, system):
    ranked = sorted(
        ((p[system], labels.get(h)) for h, p in provenance.items()
         if p.get(system) is not None and p[system] <= 10),
        key=lambda x: x[0],
    )
    gains = [(g if g is not None else 0.0) for _, g in ranked]
    dcg = sum(g / math.log2(rank + 1) for rank, g in enumerate((gg for gg in gains), start=1))
    ideal = sorted(gains, reverse=True)
    idcg = sum(g / math.log2(rank + 1) for rank, g in enumerate(ideal, start=1))
    return dcg / idcg if idcg > 0 else 0.0


# Metrics reported per system, in display order. p1/p3/p5 expose the top-rank
# behaviour (where a search engine's precision matters most); p10 is the declared
# primary; strict is the demanding secondary; ndcg is rank-aware; mrr is the mean
# reciprocal rank of the first relevant hit.
METRICS = ["p1", "p3", "p5", "p10", "p10_strict", "ndcg", "mrr"]


def metric_value(name, labels, prov_q, system):
    if name == "p1":
        return p_at_k(labels, prov_q, system, 1)
    if name == "p3":
        return p_at_k(labels, prov_q, system, 3)
    if name == "p5":
        return p_at_k(labels, prov_q, system, 5)
    if name == "p10":
        return p_at_k(labels, prov_q, system, 10)
    if name == "p10_strict":
        return p_at_k(labels, prov_q, system, 10, STRICT)
    if name == "ndcg":
        return ndcg_at_10(labels, prov_q, system)
    if name == "mrr":
        return mrr(labels, prov_q, system)
    raise ValueError(name)


# --------------------------------------------------------------------------- #
# Bootstrap CIs over queries
# --------------------------------------------------------------------------- #
def bootstrap_ci(per_query_values, n=BOOTSTRAP_N, seed=BOOTSTRAP_SEED, alpha=0.05):
    """Percentile bootstrap over the per-query values (resample queries)."""
    vals = [v for v in per_query_values if v is not None]
    if not vals:
        return {"mean": None, "lo": None, "hi": None, "n": 0}
    rng = random.Random(seed)
    k = len(vals)
    means = []
    for _ in range(n):
        sample = [vals[rng.randrange(k)] for _ in range(k)]
        means.append(sum(sample) / k)
    means.sort()
    lo = means[int((alpha / 2) * n)]
    hi = means[int((1 - alpha / 2) * n)]
    return {"mean": sum(vals) / k, "lo": lo, "hi": hi, "n": k}


# --------------------------------------------------------------------------- #
# Agreement
# --------------------------------------------------------------------------- #
def cohen_kappa(pairs):
    """pairs: list of (a, b) categorical labels (0.0/0.5/1.0). Returns kappa."""
    pairs = [(a, b) for a, b in pairs if a is not None and b is not None]
    n = len(pairs)
    if n == 0:
        return None
    cats = CATEGORIES
    po = sum(1 for a, b in pairs if a == b) / n
    pa = {c: sum(1 for a, _ in pairs if a == c) / n for c in cats}
    pb = {c: sum(1 for _, b in pairs if b == c) / n for c in cats}
    pe = sum(pa[c] * pb[c] for c in cats)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def krippendorff_alpha(matrix, metric="interval"):
    """matrix: list of units, each a list of rater values (None = missing).

    metric: 'interval' (squared numeric difference, default -- scores are
    ordered/numeric) or 'nominal' (agree/disagree).
    """
    def delta(a, b):
        return (a - b) ** 2 if metric == "interval" else (0.0 if a == b else 1.0)

    # Coincidence matrix over ordered value pairs within each unit.
    coincidence = defaultdict(float)
    for unit in matrix:
        vals = [v for v in unit if v is not None]
        m = len(vals)
        if m < 2:
            continue
        for i in range(m):
            for j in range(m):
                if i == j:
                    continue
                coincidence[(vals[i], vals[j])] += 1.0 / (m - 1)
    # Marginals and grand total come directly from the coincidence matrix.
    value_counts = defaultdict(float)
    for (a, b), c in coincidence.items():
        value_counts[a] += c
    n_total = sum(value_counts.values())
    if n_total < 2:
        return None

    do = sum(c * delta(a, b) for (a, b), c in coincidence.items()) / n_total
    values = list(value_counts)
    de = 0.0
    for a in values:
        for b in values:
            de += value_counts[a] * value_counts[b] * delta(a, b)
    de /= n_total * (n_total - 1)
    if de == 0:
        return 1.0
    return 1 - do / de


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def analyze(prov, judges, systems, human_gold=None):
    per_query = prov["per_query"]
    query_ids = sorted(per_query)

    judge_summaries = {}
    judge_medians = {}     # judge -> {(qid,doc): score}  for cross-judge alpha
    high_variance = []     # (judge, qid, doc, variance)

    for judge, repeats in judges.items():
        medians, variances = collapse_repeats(repeats)
        n_repeats = len(repeats)

        flat_med = {}
        for qid in medians:
            for doc_id, s in medians[qid].items():
                flat_med[(qid, doc_id)] = s
                v = variances[qid][doc_id]
                if v > 0:
                    high_variance.append({"judge": judge, "query_id": qid,
                                          "doc_id": doc_id, "variance": round(v, 4)})
        judge_medians[judge] = flat_med

        per_system = {s: {m: [] for m in METRICS} for s in systems}
        per_query_out = {}
        for qid in query_ids:
            prov_q = per_query[qid]["provenance"]
            id_to_hash = per_query[qid]["id_to_hash"]
            lab = labels_by_hash(medians.get(qid, {}), id_to_hash)
            per_query_out[qid] = {}
            for s in systems:
                vals = {m: metric_value(m, lab, prov_q, s) for m in METRICS}
                for m in METRICS:
                    per_system[s][m].append(vals[m])
                per_query_out[qid][s] = {m: round(vals[m], 4) for m in METRICS}

        agg = {}
        for s in systems:
            agg[s] = {m: bootstrap_ci(per_system[s][m]) for m in METRICS}
        # paired delta c2c - bm25 (only meaningful with exactly these two systems)
        deltas = {}
        if "c2c" in systems and "bm25" in systems:
            for m in METRICS:
                paired = [c - b for c, b in zip(per_system["c2c"][m], per_system["bm25"][m])]
                deltas[m] = bootstrap_ci(paired)

        judge_summaries[judge] = {
            "n_repeats": n_repeats,
            "per_query": per_query_out,
            "aggregate": agg,
            "delta_c2c_minus_bm25": deltas,
        }

    # ------- jury (across-judge) mean of per-query metrics -------
    jury = {}
    if len(judges) > 1:
        for s in systems:
            jury[s] = {}
            for m in METRICS:
                # average the per-query metric across judges, then bootstrap over queries
                per_q_avg = []
                for qid in query_ids:
                    vals = [judge_summaries[j]["per_query"][qid][s][m] for j in judges]
                    per_q_avg.append(sum(vals) / len(vals))
                jury[s][m] = bootstrap_ci(per_q_avg)

    # ------- agreement -------
    agreement = {"cohen_kappa_vs_human": {}, "krippendorff_alpha_across_judges": None}
    if human_gold:
        gold = {}
        for rec in human_gold["labels"].values():
            gold[(rec["query_id"], rec["doc_id"])] = _coerce_score(rec.get("score"))
        for judge, med in judge_medians.items():
            pairs = [(med.get(k), gold[k]) for k in gold if k in med]
            agreement["cohen_kappa_vs_human"][judge] = _round(cohen_kappa(pairs))

    if len(judges) > 1:
        all_units = set()
        for med in judge_medians.values():
            all_units |= set(med)
        matrix = []
        for unit in sorted(all_units):
            matrix.append([judge_medians[j].get(unit) for j in judges])
        agreement["krippendorff_alpha_across_judges"] = _round(krippendorff_alpha(matrix, "interval"))

    high_variance.sort(key=lambda x: -x["variance"])
    return {
        "systems": systems,
        "judges": list(judges),
        "per_judge": judge_summaries,
        "jury_mean": jury,
        "agreement": agreement,
        "high_variance_docs": high_variance,
    }


def _round(x, nd=4):
    return round(x, nd) if isinstance(x, (int, float)) else x


def _fmt_ci(ci):
    if not ci or ci["mean"] is None:
        return "   n/a"
    return f"{ci['mean']:.3f} [{ci['lo']:.3f}, {ci['hi']:.3f}]"


def print_report(report):
    systems = report["systems"]
    print("\n" + "=" * 78)
    print("BLINDED LLM-AS-A-JUDGE - RESULTS")
    print("=" * 78)
    for judge, s in report["per_judge"].items():
        print(f"\nJudge: {judge}   (repeats={s['n_repeats']})")
        print(f"  {'metric':<12}" + "".join(f"{sys:>26}" for sys in systems))
        for m in METRICS:
            row = f"  {m:<12}"
            for sys in systems:
                row += f"{_fmt_ci(s['aggregate'][sys][m]):>26}"
            print(row)
        if s["delta_c2c_minus_bm25"]:
            print("  delta (c2c - bm25), mean [95% CI]:")
            for m, ci in s["delta_c2c_minus_bm25"].items():
                print(f"    {m:<10} {_fmt_ci(ci)}")

    if report["jury_mean"]:
        print("\nJury mean (across judges), per metric, mean [95% CI]:")
        for sys in systems:
            print(f"  {sys}:")
            for m in METRICS:
                print(f"    {m:<10} {_fmt_ci(report['jury_mean'][sys][m])}")

    ag = report["agreement"]
    print("\nAgreement:")
    if ag["cohen_kappa_vs_human"]:
        for judge, k in ag["cohen_kappa_vs_human"].items():
            print(f"  Cohen kappa vs human - {judge}: {k}")
    else:
        print("  Cohen kappa vs human: (no --human-gold provided)")
    print(f"  Krippendorff alpha across judges (interval): {ag['krippendorff_alpha_across_judges']}")

    hv = report["high_variance_docs"]
    print(f"\nHigh-variance (ambiguous) documents: {len(hv)}")
    for d in hv[:15]:
        print(f"  {d['judge']}  {d['query_id']}/{d['doc_id']}  var={d['variance']}")
    if len(hv) > 15:
        print(f"  ... and {len(hv) - 15} more (see report JSON)")
    print("=" * 78 + "\n")


def main():
    try:                       # keep console output UTF-8 clean on Windows
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judging-dir", default=os.path.join(HERE, "judging"),
                    help="directory holding pool_provenance.json (default: ./judging)")
    ap.add_argument("--outputs", default=None,
                    help="directory of judge label files (default: <judging-dir>/judge_outputs)")
    ap.add_argument("--human-gold", default=None,
                    help="human_gold.json for Cohen's kappa (optional)")
    ap.add_argument("--report", default=None,
                    help="path to write the full report JSON (default: <judging-dir>/analysis_report.json)")
    args = ap.parse_args()

    prov_path = os.path.join(args.judging_dir, "pool_provenance.json")
    prov = load_provenance(prov_path)
    systems = prov["systems"]

    outputs_dir = args.outputs or os.path.join(args.judging_dir, "judge_outputs")
    label_paths = sorted(glob.glob(os.path.join(outputs_dir, "*.json")))
    if not label_paths:
        raise SystemExit(
            f"No judge label files found in {outputs_dir}. Expected one JSON per "
            f"(judge, repeat), e.g. <judge>__rep1.json. See analyze_labels.py docstring.")
    judges = load_label_files(label_paths)

    human_gold = None
    if args.human_gold:
        with open(args.human_gold, encoding="utf-8") as f:
            human_gold = json.load(f)

    report = analyze(prov, judges, systems, human_gold)
    report["provenance_prompt_hash"] = prov.get("prompt_hash")
    report["provenance_seed"] = prov.get("seed")
    report["provenance_order"] = prov.get("order")

    report_path = args.report or os.path.join(args.judging_dir, "analysis_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print_report(report)
    print(f"Full report written to {report_path}")


if __name__ == "__main__":
    main()
