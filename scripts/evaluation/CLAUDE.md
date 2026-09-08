# Blinded LLM-as-a-Judge Evaluation

How we grade retrieval quality for the Code2Code semantic retriever against the
BM25 lexical baseline, without letting the judge know which system produced any
snippet. The judge only ever labels an anonymised, pooled, shuffled set of
candidates; **all system identity, ranks, scores, filenames, and metric
computation live in Python, never in the model.**

This replaces the earlier single-judge, non-blinded prompt (which showed the two
ranked lists side by side and asked the model to compute P@10 itself — both a
presentation-bias risk and an arithmetic-in-the-model risk).

## Files

| File | Role |
|------|------|
| `blind_pool.py` | Pool + dedup + shuffle the two systems' top-10 per query; render one blinded prompt per query; write the provenance answer key. |
| `judge_prompt_template.md` | The clean judge prompt. No "two systems", "semantic", "BM25", filenames, or ranks anywhere. `blind_pool.py` fills in `{QUERY_CODE}`, `{CANDIDATES}`, `{QUERY_ID}`. |
| `run_judge_api.py` | Send the blinded prompts to a judge model's API (Gemini, or any OpenAI-compatible endpoint: Kimi/OpenRouter/DeepSeek/GPT). Reads the API key from a git-ignored `.env`, retries on 429/5xx, resumes. Writes raw per-query responses. |
| `assemble_judge_output.py` | Parse raw judge responses (tolerates ```fences```, preamble, bare-number scores, wrong/echoed `query_id`), validate against the answer key, write the canonical `judge_outputs/<judge>__rep<k>.json`. |
| `analyze_labels.py` | Re-join the judge's `doc_id` labels to the hidden provenance; compute P@10 (lenient/strict), nDCG@10, 95% CIs (mean ± 1.96·SE over queries), per-doc variance, Cohen's κ, Krippendorff's α. |
| `.env` (git-ignored) | API keys as `NAME="value"` lines (e.g. `GOOGLE_API_KEY`, `OPENROUTER_API_KEY`). Ignored via `.gitignore`; never committed, never passed on the command line. |
| `judging/pool_provenance.json` | The answer key: `doc_id → hash`, `hash → {bm25 rank, c2c rank}`, pooled doc text, seed, and prompt hash. **Never shown to a judge.** |
| `judging/judge_inputs/prompt_<QID>.md` | The blinded prompt actually sent to each judge, per query. |
| `judging/judge_outputs/<judge>__rep<k>.json` | Each judge's finalized labels (3 judges: `claude-opus-4-8`, `gemini-3.8-flash`, `kimi-k2`). |

## Pipeline

### 1. Build the blinded pools

```bash
python scripts/evaluation/blind_pool.py --gold-sample 80
```

For each of the 27 queries this pools both systems' top-10, deduplicates
byte-identical snippets across systems by a content hash (so a snippet returned
by *both* systems gets **one** `doc_id` and **one** label — removing a real
source of noise and preventing the same snippet scoring 1.0 for one system and
0.5 for the other), shuffles with a per-query reproducible seed
(`f"{seed}:{query_id}"`), and writes one self-contained prompt per query. The
`--gold-sample N` flag additionally emits a random cross-query sample of pooled
docs (`gold_sheet.md` + `gold_template.json`) for human agreement labelling.

Original ranks live only in `pool_provenance.json` and are re-joined after
labelling. Verify no leakage before sending: any match for `bm25`, `filepath`,
etc. in a prompt must come from the candidate *code itself*, never from
harness-injected metadata.

### 2. Run each judge (blinded)

Send each `judging/judge_inputs/prompt_<QID>.md` to each judge model. The judge
returns raw JSON per the template:

```json
{"query_id": "A1", "labels": {"d001": {"score": 1.0, "rationale": "..."}, ...}}
```

Collect a run's per-query responses into one file per **(judge, repeat)** under
`judging/judge_outputs/`, named `<judge>__rep<k>.json`:

```json
{
  "judge": "claude-opus-4-8-20260601",
  "repeat": 1,
  "temperature": 0.0,
  "seed": 20260824,
  "prompt_hash": "87dca51ccb6b5a48",
  "labels": {"A1": {"d001": {"score": 1.0}, ...}, "A2": {...}}
}
```

**How the Claude judge was run (reproducibility note).** The Claude Opus 4.8
labels in `judge_outputs/claude-opus-4-8__rep1.json` were produced *inside this
repo* without any external API: one blinded sub-agent per query, each in a fresh
context that inherits nothing from the harness-building session, instructed to
read **only** its own `judge_inputs/prompt_<QID>.md` (verified: exactly one file
read per query, so no sub-agent ever saw `pool_provenance.json` or prior scores)
and return the raw JSON. This keeps the Claude judge genuinely blind even though
the orchestrator is not. A second judge from a different model family (e.g.
Gemini or Kimi, via their APIs) is still required so Krippendorff's α is defined.

**Running other judges via API.** Put keys in a git-ignored `.env`
(`GOOGLE_API_KEY="..."`, `OPENROUTER_API_KEY="..."`); `run_judge_api.py` loads it
automatically — never pass a key on the command line. Test with `--limit 1`
first, then run the full 27 with a polite `--sleep` for free-tier rate limits.

```bash
# Gemini (Google AI Studio). NB: gemini-*-pro is billing-gated on the free tier;
# a current-generation *-flash (e.g. gemini-3.7-flash) is free and a strong judge.
python scripts/evaluation/run_judge_api.py --provider gemini --model gemini-3.7-flash \
    --api-key-env GOOGLE_API_KEY --out-raw scripts/evaluation/judging/raw_gemini --sleep 12
python scripts/evaluation/assemble_judge_output.py --judge gemini-3.7-flash \
    --raw-dir scripts/evaluation/judging/raw_gemini --temperature 0

# Kimi K2 via OpenRouter (one key, many models; --max-tokens caps the provider limit)
python scripts/evaluation/run_judge_api.py --provider openai \
    --base-url https://openrouter.ai/api/v1 --model moonshotai/kimi-k2 \
    --api-key-env OPENROUTER_API_KEY --out-raw scripts/evaluation/judging/raw_kimi --sleep 12
python scripts/evaluation/assemble_judge_output.py --judge kimi-k2 \
    --raw-dir scripts/evaluation/judging/raw_kimi --temperature 0
```

`run_judge_api.py` skips already-written queries, so a run interrupted by a
rate-limit/503 simply resumes on re-run. `assemble_judge_output.py` validates
every `doc_id` against the answer key and falls back to the filename for the
query id when a judge echoes a wrong/placeholder `query_id`.

Rules for this step:

* **Pin dated model IDs, never `-latest` aliases.**
* **3 samples per (query, judge).** `analyze_labels.py` takes the median label
  per document and logs per-document label variance (the high-variance docs are
  the ambiguous cases for the paper's error analysis).
* Record the judge model ID, temperature, seed, and prompt hash on every run
  (the fields above).

### 3. Human gold + agreement — *before you trust any of it*

Hand-label the 50–100 pooled docs in `gold_sheet.md`, transcribe scores into
`gold_template.json`, save it as `judging/human_gold.json`. Only after the
agreement numbers exist should the P@10 comparison be reported.

### 4. Compute metrics (in code, never in the model)

```bash
python scripts/evaluation/analyze_labels.py --human-gold judging/human_gold.json
```

Reports, **per judge** and as the jury mean:

* **P@10 lenient** — fraction of the top-10 with median score `>= 0.5`.
* **P@10 strict** — fraction with median score `== 1.0`.
* **nDCG@10** — rank-aware.
* **95% CIs over queries** (normal approximation: mean ± 1.96·SE; not just point
  estimates), for each system and for the paired `c2c − bm25` delta.
* **Cohen's κ** of each judge against the human gold labels.
* **Krippendorff's α** across judges over the full pooled set.

A result that holds under *every* judge is a different, stronger claim than one
that holds on average — so report per-judge numbers, not only the jury mean.

**Interpreting the three metrics (they measure different things — don't
conflate them).**

* **P@10 strict** (fraction of top-10 scored exactly 1.0) is deliberately harsh:
  1.0 requires the *same computational task*, so partial/variant/helper matches
  (the common case in a large heterogeneous corpus) score 0.5 and don't count.
  Low absolute strict values are expected and are a property of the rubric, not
  a system failure — report them, but they are a **secondary** lens, not the
  headline.
* **P@10 lenient** (`>= 0.5`) is the **declared primary** precision metric: is a
  top-10 result topically relevant at all.
* **nDCG@10** is rank-aware but **self-normalised within each system's own
  retrieved 10** (IDCG is the ideal ordering of *those* items). So it measures
  *ordering quality of what was returned*, not recall against the corpus, and it
  runs high when a list's relevance is fairly uniform. The **difference** between
  systems is the informative part; do not sell the absolute height as coverage.

`analyze_labels.py` also reports **P@1/P@3/P@5** and **MRR** (top-rank precision,
where a search engine matters most). Read the CIs, not just the point
estimates: at n=27 queries, **nDCG@10 is the only delta significant across all
judges**; P@5/P@10 are significant on the stricter-vs-lenient majority; and
**P@1/P@3/MRR have large point estimates but wide CIs** (a 0/1-per-query metric
is high-variance at this n) — report them as consistent *supporting* evidence
(all judges agree in direction and magnitude), not as significant on their own.

Lead the write-up with **nDCG@10 + lenient P@5/P@10**; present strict P@10 as the
demanding secondary metric and P@1/P@3/MRR as directional support. Match the claim
to the CIs — a modest but significant, judge-robust improvement in ranking and
lenient precision is the defensible story, not a blowout. **Declare the small
benchmark size (27 queries)** as the main limit on statistical power — it is `n`,
not the metric, that widens the top-rank CIs.

### 5. Sanity check for residual presentation bias

```bash
python scripts/evaluation/blind_pool.py --order c2c --out-dir judging_c2corder
```

Re-grade a subset with the pool ordered by C2C rank instead of shuffled. If the
blinded and unblinded numbers diverge materially, part of what you are measuring
is presentation, not retrieval.

### 6. Qualitative error analysis (grounded in the frozen labels)

For the paper's failure-mode narrative, do **not** ask a model to *describe* what
happened — that reintroduces a generation step that can hallucinate. Instead read
the failure modes straight off the frozen data: re-join each judge's `doc_id`
labels to `pool_provenance.json` to recover, per query and per system, the actual
function retrieved at each rank and the score all three judges gave it. Every
per-query claim in the write-up ("BM25 returns `parseFile` at rank 1, scored 0.0
by all judges; C2C returns `safeFileHash`, 1.0") is then a fact checkable in the
labels, not a model's retelling. (An earlier version of this step fed both ranked
lists back to an LLM for a prose summary; it was removed because label-grounded
extraction is strictly more defensible and needs no un-blinding of a model.)

## Few-shot anchors (optional)

Prepend 3–4 labelled examples from the hand-labelled gold set, chosen so outcomes
are mixed (at least one 1.0, one 0.5, one 0.0) and drawn from queries **not** in
the evaluation set. Never use an example whose pattern of scores resembles the
result you expect.

## What to declare in the write-up

* **Relevance is defined cross-language**: a snippet implementing the same task
  in a different language scores 1.0. This is a property of the benchmark's
  notion of user need and *structurally advantages semantic retrieval over
  lexical matching* — state it explicitly rather than letting a reviewer find it.
* Judges are blinded to system identity; pooling, deduplication, and shuffling
  are as described above.
* Report per-judge κ against human labels, inter-judge α, and metrics per judge —
  not only the jury mean.

## Relevance scale (the rubric the judge applies)

- **1.0 — Relevant.** Same computational task, or a correct specific solution for
  the query's intent. Naming/style/language differences do not reduce relevance.
- **0.5 — Partially relevant.** Topically related: partial, non-idiomatic, or the
  target logic appears only as a helper step in a larger function.
- **0.0 — Irrelevant.** Does not address the task, or overlaps only superficially
  (shared identifiers like `mid`/`min` while doing something unrelated).
- **null — Cannot determine.** Too truncated/context-dependent to judge. Sparingly.
