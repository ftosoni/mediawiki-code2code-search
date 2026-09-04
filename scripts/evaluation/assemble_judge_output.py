"""Assemble raw per-query judge responses into one canonical label file.

A judge (Gemini, Kimi, DeepSeek, GPT, ...) returns, per query, raw JSON like

    {"query_id": "A1", "labels": {"d001": {"score": 1.0, "rationale": "..."}, ...}}

possibly wrapped in ```json fences or with stray preamble. This script collects
those responses, extracts the JSON robustly, validates them against the blinding
answer key (``pool_provenance.json``), and writes

    judge_outputs/<judge>__rep<k>.json

in exactly the format ``analyze_labels.py`` expects.

Input can be either a directory of response files (one or more per query; the
query id is read from the JSON, or inferred from the filename) or a single file
containing several JSON objects concatenated / one-per-line.

Usage
-----
    python assemble_judge_output.py --judge gemini-2.5-flash --raw-dir judging/raw_gemini
    python assemble_judge_output.py --judge kimi-k2 --raw-file judging/kimi_all.txt --repeat 1
    # tolerate an incomplete run (fill any missing doc with null, drop extras):
    python assemble_judge_output.py --judge gemini-2.5-flash --raw-dir judging/raw_gemini --fill-missing
"""
import argparse
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LEGAL = (0.0, 0.5, 1.0, None)


def strip_fences(text: str) -> str:
    # remove ```json ... ``` or ``` ... ``` wrappers if present
    text = re.sub(r"```[a-zA-Z0-9_]*\s*", "", text)
    return text.replace("```", "")


def extract_json_objects(text: str):
    """Yield every top-level {...} block in ``text`` that parses as JSON and
    contains a 'labels' key. Brace-matching scan, so preamble/suffix is ignored."""
    text = strip_fences(text)
    depth = 0
    start = None
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    chunk = text[start:i + 1]
                    try:
                        obj = json.loads(chunk)
                    except json.JSONDecodeError:
                        obj = None
                    if isinstance(obj, dict) and "labels" in obj:
                        yield obj
                    start = None


def coerce_score(s):
    if s is None:
        return None
    if isinstance(s, str):
        s = s.strip().lower()
        if s in ("null", "none", "nan", ""):
            return None
        s = float(s)
    s = float(s)
    if s in (0.0, 0.5, 1.0):
        return s
    return min((0.0, 0.5, 1.0), key=lambda c: abs(c - s))   # snap stray values


def normalize_labels(raw_labels):
    """{doc_id: {score,...}} or {doc_id: score} -> {doc_id: score}."""
    out = {}
    for doc_id, v in raw_labels.items():
        score = v.get("score") if isinstance(v, dict) else v
        out[doc_id] = coerce_score(score)
    return out


def infer_qid(filename, known_qids):
    base = os.path.basename(filename)
    for qid in sorted(known_qids, key=len, reverse=True):
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(qid)}(?![0-9])", base):
            return qid
    return None


def collect(raw_paths, known_qids):
    """Return {qid: {doc_id: score}} merged from all raw files (last wins)."""
    collected = {}
    for path in raw_paths:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        objs = list(extract_json_objects(text))
        if not objs:
            print(f"  [warn] no JSON object with 'labels' found in {os.path.basename(path)}")
            continue
        for obj in objs:
            # Trust the JSON's query_id only if it is a known id; otherwise fall
            # back to inferring it from the filename (judges sometimes echo a
            # placeholder like "query" or the wrong id).
            qid = obj.get("query_id")
            if qid not in known_qids:
                inferred = infer_qid(path, known_qids)
                if inferred and qid not in known_qids:
                    if qid is not None:
                        print(f"  [fixed] {os.path.basename(path)}: query_id {qid!r} "
                              f"not recognised, using {inferred} from filename")
                    qid = inferred
            if qid not in known_qids:
                print(f"  [warn] {os.path.basename(path)}: unknown/could-not-infer query_id "
                      f"({obj.get('query_id')!r}); skipping")
                continue
            collected[qid] = normalize_labels(obj["labels"])
    return collected


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--judge", required=True, help="dated judge id, e.g. gemini-2.5-flash")
    ap.add_argument("--raw-dir", help="directory of raw per-query response files")
    ap.add_argument("--raw-file", nargs="+", help="one or more files containing raw JSON responses")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--judging-dir", default=os.path.join(HERE, "judging"))
    ap.add_argument("--temperature", type=float, default=None, help="record the judge temperature")
    ap.add_argument("--fill-missing", action="store_true",
                    help="fill any missing doc_id with null and drop extras instead of erroring")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    prov = json.load(open(os.path.join(args.judging_dir, "pool_provenance.json"), encoding="utf-8"))
    known_qids = set(prov["per_query"])

    paths = []
    if args.raw_dir:
        paths += sorted(glob.glob(os.path.join(args.raw_dir, "*")))
    if args.raw_file:
        paths += args.raw_file
    paths = [p for p in paths if os.path.isfile(p)]
    if not paths:
        raise SystemExit("No raw input files. Pass --raw-dir and/or --raw-file.")

    print(f"Reading {len(paths)} raw file(s)...")
    collected = collect(paths, known_qids)

    # ---- validate / reconcile against the answer key ----
    errors = []
    labels = {}
    for qid, q in prov["per_query"].items():
        expected = set(q["id_to_hash"])
        got = collected.get(qid)
        if got is None:
            errors.append(f"{qid}: no response found")
            if args.fill_missing:
                labels[qid] = {d: None for d in expected}
            continue
        missing = expected - set(got)
        extra = set(got) - expected
        if missing or extra:
            msg = f"{qid}: missing={sorted(missing)} extra={sorted(extra)}"
            if args.fill_missing:
                for d in missing:
                    got[d] = None
                for d in extra:
                    got.pop(d, None)
                print(f"  [fixed] {msg}")
            else:
                errors.append(msg)
        labels[qid] = {d: got.get(d) for d in expected}

    if errors and not args.fill_missing:
        print("\nVALIDATION ERRORS (re-run with --fill-missing to tolerate, or fix the raw files):")
        for e in errors:
            print("  ", e)
        raise SystemExit(1)

    obj = {
        "judge": args.judge,
        "repeat": args.repeat,
        "temperature": args.temperature,
        "seed": prov.get("seed"),
        "prompt_hash": prov.get("prompt_hash"),
        "labels": {qid: {d: {"score": s} for d, s in labels[qid].items()} for qid in labels},
    }
    out = args.out or os.path.join(args.judging_dir, "judge_outputs",
                                   f"{args.judge}__rep{args.repeat}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(obj, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    n = sum(len(v) for v in labels.values())
    print(f"\nOK: {len(labels)}/{len(known_qids)} queries, {n} labels -> {out}")
    if args.fill_missing and errors:
        print(f"({len(errors)} query/doc gaps were filled with null - check the run was complete.)")


if __name__ == "__main__":
    main()
