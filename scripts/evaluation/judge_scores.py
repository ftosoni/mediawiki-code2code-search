"""
Manual P@10 relevance judgments by a single judge (Claude Opus 4.8),
adjudicated over the POOLED top-10 results of BM25 and Code2Code for each
of the 27 benchmark queries.

Graded relevance scale (per manuscript Table tab:relevance_scale):
    1.0  Relevant           - implements the same computational task / correct
                              specific solution for the query intent.
    0.5  Partially relevant - topically related; partial or non-idiomatic
                              realisation, or uses the target logic as a step.
    0.0  Irrelevant         - does not solve the problem / unrelated.

P@10 (primary metric, per manuscript methodology) = fraction of the top-10
results with graded score >= 0.5.

Each list below holds the 10 graded scores for ranks 1..10, in order.
A short rationale per query is kept in COMMENTS for transparency.

Code2Code results adjudicated here are the LOCAL run
(evaluation_results_127_0_0_1_8000_search_7runs.json); 18 of the 27 C2C lists
are byte-identical to the earlier Toolforge run, while 9 differ
(A5, B3, B7, B10, B11, C3, C4, D1, D2) and were re-judged on the local snippets
-- of those, A5 and C4 still score all-1.0. BM25 lists are unchanged.
"""

import json
import os

# scores[system][qid] = [s1..s10]
BM25 = {}
C2C = {}
COMMENTS = {}

# ===================== CATEGORY A — Canonical algorithms =====================
# A1 GCD (Python)
BM25["A1"] = [0.5, 1, 0.5, 0.5, 0, 0, 0, 0, 0, 0]
C2C["A1"]  = [1, 1, 1, 1, 1, 1, 1, 0.5, 1, 0.5]
COMMENTS["A1"] = ("BM25: r2 exact recursive gcd; r1/r3/r4 use gcd as a step "
    "(aspect-ratio, fraction reduce/format); r5 tests the '\\gcd' MathML token; "
    "r6-10 are sqlite time-scaling helpers with a bit-trick var named gcd (not GCD). "
    "C2C: r1-7,9 are real GCD impls (binary/Euclidean); r8 MS-Graph Gcd API wrapper, "
    "r10 LCM-via-gcd (partial).")

# A2 Binary search (JavaScript)
BM25["A2"] = [1, 1, 1, 1, 1, 0, 0, 0, 0, 1]
C2C["A2"]  = [1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5]
COMMENTS["A2"] = ("BM25: r1-5,10 genuine binary searches; r6-9 'heComes' zalgo "
    "text generator (matched on 'mid'). C2C: r1-9 all binary search variants; "
    "r10 linear byte arrayIndexOf (partial - different algorithm).")

# A3 String truncation with ellipsis (PHP)
BM25["A3"] = [1, 0, 0.5, 1, 0.5, 1, 1, 1, 1, 1]
C2C["A3"]  = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
COMMENTS["A3"] = ("BM25: r2 string-similarity score (irrelevant); r3 column "
    "formatter and r5 pattern highlighter only partially truncate. C2C: all 10 "
    "are truncate/ellipsis/substr-to-maxlen functions.")

# A4 JSON encode with error forwarding (Go)
BM25["A4"] = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
C2C["A4"]  = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
COMMENTS["A4"] = ("Tie at ceiling. Go MarshalJSON/Encode functions share highly "
    "discriminative tokens (json, Marshal, Errorf, err, byte) so BM25 matches the "
    "same family C2C retrieves: all 10 of both are json-encode-with-error-return.")

# A5 Retry with exponential back-off (Python)
BM25["A5"] = [1, 1, 1, 0.5, 1, 1, 0.5, 0.5, 1, 1]
C2C["A5"]  = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
COMMENTS["A5"] = ("BM25: r4 is the backoff-delay helper only (partial); r7 upload "
    "and r8 add-description embed a retry loop (partial); rest are retry wrappers. "
    "C2C (local): all 10 are genuine retry wrappers/loops -- retry_on_failure and "
    "retry_function decorators, pip retry(wait, stop_after_delay), wmflib "
    "retry(backoff_mode='exponential', true exp backoff), and jaraco retry_call "
    "(r7-10 byte-identical copies); duplicate-heavy but all relevant.")

# ===================== CATEGORY B — Name-obfuscated semantics =================
# B1 Permission check canUserEdit (PHP)
BM25["B1"] = [0, 1, 0, 1, 1, 1, 1, 1, 1, 1]
C2C["B1"]  = [1, 1, 1, 0.5, 1, 1, 1, 1, 1, 0]
COMMENTS["B1"] = ("Weak gap: query body keeps standard tokens (isAllowed, isProtected, "
    "edit, Title, User). BM25 r1/r3 are tests (0); rest are genuine userCan/permission checks. "
    "C2C r10 pushEdit records an edit (0), r4 abuse-filter check (0.5).")

# B2 Debounce delayExecution (JS)
BM25["B2"] = [0.5, 1, 0.5, 0.5, 0.5, 0.5, 1, 0.5, 0.5, 1]
C2C["B2"]  = [0.5, 0.5, 1, 1, 1, 1, 0.5, 1, 1, 0.5]
COMMENTS["B2"] = ("Tie: body has setTimeout/clearTimeout/timer (debounce+throttle family). "
    "Throttle graded 0.5 (related rate-limiter, not true debounce); true debounce=1; "
    "bare delay/sleep helpers 0.5.")

# B3 Session invalidation invalidateUserSession (PHP)
BM25["B3"] = [1, 1, 1, 0.5, 0, 0, 1, 1, 1, 0.5]
C2C["B3"]  = [1, 0.5, 0.5, 1, 1, 1, 0.5, 0.5, 0, 0.5]
COMMENTS["B3"] = ("Body uses exact method names (setToken, saveSettings, "
    "invalidateSessionsForUser). BM25 r5/r6 are InvalidateUserSessions tests (0). "
    "C2C (local): r1 SessionManager::invalidateSessionsForUser is the exact analog; "
    "r4 invalidateForUser and r5/r6 CentralAuth provider impls are genuine (1); r2 "
    "interface decl and r3 empty overridable stub graded 0.5; r7/r8 maintenance "
    "classes (TerminateUserSession, InvalidateUserSessions) 0.5 (class-level); r9 "
    "ProfileImage unset 0 (unrelated); r10 invalidateUsersRightsCache 0.5 (per-user "
    "cache, different subsystem).")

# B4 LRU eviction evict_oldest (Python) -- STRONG GAP
BM25["B4"] = [0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0]
C2C["B4"]  = [0.5, 1, 1, 0.5, 0.5, 0.5, 1, 0.5, 1, 0.5]
COMMENTS["B4"] = ("Strong semantic gap. BM25 matched 'cache' -> stats getters, "
    "constructors, tests, copy_cache (no eviction). C2C surfaces the true eviction "
    "policies at top: evictLRU, evictByMemoryPressure, pruneExcessStashedEntries(oldest), "
    "removeOldest; generic single-key cache deletes graded 0.5.")

# B5 Rate-limit gate isRateLimited (PHP) -- STRONG GAP
BM25["B5"] = [0.5, 0, 0.5, 0.5, 0.5, 0, 0, 0, 0, 0]
C2C["B5"]  = [1, 0.5, 0.5, 1, 1, 0.5, 1, 0.5, 1, 0.5]
COMMENTS["B5"] = ("Strong gap. BM25 matched 'cache/makeKey/get/count' -> stash counters, "
    "mentee caches, locked-page checks, 2 RateLimiter tests (0). C2C finds the real gates: "
    "doPingLimiter, isThrottled, passCaptchaLimited, UserAuthority::internalAllowed.")

# B6 Error normaliser toError (TS) -- STRONGEST GAP
BM25["B6"] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
C2C["B6"]  = [1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
COMMENTS["B6"] = ("Strongest gap. BM25 matched Error/JSON.stringify/typeof/value -> "
    "config validators and AST-node builders that THROW errors: zero normalise a value to "
    "an Error. C2C r1 getError = exact analog of toError; r2-10 are one error-formatting "
    "util (Error.prototype.toString) duplicated across repos (graded 0.5, duplicate-heavy tail).")

# B7 URL slug make_slug (Python)
BM25["B7"] = [0.5, 1, 1, 0.5, 0.5, 0.5, 0, 0, 0, 0]
C2C["B7"]  = [1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0]
COMMENTS["B7"] = ("Weak gap: shared 'slug/title' tokens. BM25 finds 2 exact slugify; both "
    "pollute with title CRUD/tests. C2C (local): r1 slugifyTitle (JS) is an exact "
    "cross-language slug (1); r2-r9 are the title-normalisation family (buildTitle, "
    "normalize, pageTitleForMW, makePrefix, to_url_format, normalize_title, "
    "normalizedFilename, cleanName) -- space/underscore/lowercase/trim munging, not a "
    "hyphen slug -- graded 0.5; r10 _fixSpecialName (special-page alias) 0.")

# B8 CAPTCHA verify (PHP) -- STRONG GAP
BM25["B8"] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5]
C2C["B8"]  = [1, 1, 0.5, 0.5, 0.5, 0, 0, 0, 0.5, 1]
COMMENTS["B8"] = ("Strong gap. BM25 matched 'token/expected' -> parser/lexer token scanners "
    "and CSRF-token tests; only r10 (token store get+delete) is mechanically close. "
    "C2C finds passCaptcha (exact), Turnstile captcha, TOTPKey::verify, Token::match.")

# B9 Worker pool processWithPool (Go)
BM25["B9"] = [0, 1, 0, 0, 1, 0, 1, 0.5, 0, 0]
C2C["B9"]  = [0.5, 0, 1, 1, 1, 0.5, 1, 0.5, 1, 0]
COMMENTS["B9"] = ("BM25 matched chan/errs/struct -> fsnotify channel constructors (0); "
    "found AggregateGoroutines, ParallelizeUntil, compress4Xp (parallel+errs). C2C surfaces "
    "worker pools (startWorkers, pool.Run, ParallelizeUntil, processBlocks); r2 test, r10 type-only (0).")

# B10 Recursive category subtree getDescendants (PHP)
BM25["B10"] = [1, 1, 1, 1, 1, 0.5, 0.5, 0.5, 0.5, 0.5]
C2C["B10"]  = [1, 0.5, 1, 1, 1, 1, 0.5, 0.5, 0.5, 0]
COMMENTS["B10"] = ("Body keeps structural tokens (depth, children, categorylinks, subcat). "
    "Both find recursive subtree/subcat collectors. C2C (local): r1 fetchSubCategories "
    "(Java), r3 addSubCategories, r4 buildCategoryHierarchy (JS), r5 getSubCategoriesFromPath, "
    "r6 populateChildren are genuine recursive category-subtree collectors (1); r2 "
    "DetectCategoryRecursion class 0.5 (recursive subcat walk for cycle detection); r7/r9 "
    "getChildren of doc sections/comments and r8 assignLevel (generic recursive tree walk) "
    "0.5; r10 d3 node_descendants one-liner 0.")

# B11 Paginated API fetch fetch_all_pages (Python)
BM25["B11"] = [1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0, 1]
C2C["B11"]  = [1, 1, 1, 1, 0.5, 0, 0.5, 0.5, 0.5, 0.5]
COMMENTS["B11"] = ("Shared offset/limit/page_size/requests tokens. BM25 r1 & r10 loop all "
    "pages (1); single-page web routes graded 0.5. C2C (local): r1 _get_all_pages, r2 "
    "query_with_continue, r3 _paginated, r4 _paginate_once (limit/offset loop) are true "
    "fetch-all loops (1); r5 fetch_batch, r7/r8 PagePile query, r9 _fetch_chunk, r10 "
    "SearchPageGenerator are single-page/partial (0.5); r6 _fetch_pending_pages (DB, no "
    "pagination) 0.")

# B12 HTTP retry on 5xx doWithRetry (Go) -- GAP
BM25["B12"] = [0, 0, 0, 0.5, 1, 0.5, 0, 0, 1, 0]
C2C["B12"]  = [0.5, 0.5, 0.5, 0.5, 1, 0.5, 0, 1, 1, 1]
COMMENTS["B12"] = ("Gap. BM25 matched http.Client/client.Do/StatusCode -> mostly single-shot "
    "HTTP calls (fetchIMDSToken, loadHTTPBytes, DownloadFileAuth = 0); 2 genuine retry loops "
    "(Watch, Stream). C2C finds retry logic: WithRetry, retry-loop, shouldRetryRequest (x3); "
    "r7 doNoRetry = 0.")

# ===================== CATEGORY C — Cross-language ===========================
# C1 SHA-256 file hash (PHP -> Go/Python) -- STRONG GAP
BM25["C1"] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
C2C["C1"]  = [1, 1, 0.5, 1, 0.5, 1, 0.5, 0.5, 0.5, 1]
COMMENTS["C1"] = ("Strong gap (even same-language). BM25 matched 'filepath/string' -> "
    "path-manipulation, chmod, ini-parse, parser-functions: zero file hashers. C2C finds "
    "file-content hashers (safeFileHash, sha1_file, md5_file/ETag); object/string hashers 0.5.")

# C2 ISO-8601 date parsing (Python -> PHP/JS)
BM25["C2"] = [1, 1, 1, 0.5, 0, 0, 0.5, 0.5, 0.5, 0.5]
C2C["C2"]  = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
COMMENTS["C2"] = ("C2C wins precision: r1/r2/r4 are the exact fromisoformat(+Z) analog; "
    "BM25 finds Python strptime date parsers (within-language). NOTE: neither surfaced the "
    "stated PHP/JS cross-language targets -- both returned Python only.")

# C3 Fan-out / parallel map (Go -> JS Promise.all) -- HARD FOR BOTH
BM25["C3"] = [0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0]
C2C["C3"]  = [0, 0, 0, 1, 0, 0, 0, 0, 1, 0.5]
COMMENTS["C3"] = ("Hard for both; corpus lacks a clean fan-out-collect analog and NO JS "
    "Promise.all surfaced. BM25 matched chan/errs/wg -> Go concurrency plumbing. C2C "
    "(local): r4 conc.ForEachIdx and r9 conc.Map are genuine parallel maps over an input "
    "slice (1); r10 Broadcaster.distribute is event fan-out to watchers (0.5); r1-3,5-8 are "
    "SIMD-hash channel/lane servers, prometheus collectors, a log demux and a workqueue "
    "wait -- concurrency plumbing, not fan-out-collect (0).")

# C4 Throttle / call-rate limiter (TS -> PHP)
BM25["C4"] = [1, 1, 1, 1, 0.5, 1, 1, 1, 1, 1]
C2C["C4"]  = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
COMMENTS["C4"] = ("Tie at ceiling. 'throttle/lastCall/Date.now/setTimeout' highly discriminative; "
    "corpus is full of JS/TS throttles. C2C (local): all 10 are genuine throttle "
    "(leading-edge rate limiter) implementations -- r6/r7/r8 the same leaflet throttle and "
    "r9/r10 the same Sortable _throttle (duplicate-heavy), but every hit is a true throttle. "
    "BM25 r5 is a throttle-internal helper (0.5).")

# C5 Recursive table/dict serialiser (Lua -> Python/PHP) -- BM25 WIN
BM25["C5"] = [1, 1, 1, 1, 1, 0.5, 1, 1, 1, 0.5]
C2C["C5"]  = [0, 0, 1, 0, 0, 0.5, 0, 0, 0.5, 1]
COMMENTS["C5"] = ("BM25 WIN. Lua-idiom tokens (table, pairs, indent, tostring, serialize) let "
    "BM25 retrieve the real recursive dumpers (print_r, deepToString, dumpObject) plus PHP "
    "cross-language serialisers (JsonLdRdfWriter, formatVar). C2C drifted to Wikibase "
    "snak/value RENDERERS (formatValue/renderSnak delegate to php.X, not table dumping) = 0; "
    "only LuaSerializer & JsonLdRdfWriter are true serialisers. Bi-encoder misled by domain vocab.")

# C6 Wikidata SPARQL query runner (Python -> PHP/JS)
BM25["C6"] = [0.5, 0.5, 0.5, 0.5, 1, 0.5, 1, 0.5, 0.5, 0.5]
C2C["C6"]  = [1, 1, 1, 1, 0.5, 1, 0.5, 0.5, 1, 1]
COMMENTS["C6"] = ("Tie by >=0.5 metric but C2C far higher precision: C2C returns 7 true SPARQL "
    "runners (retrieve_query, get_sparql_query_results, query_wikidata, SparqlBase, WcqsSession, "
    "SparqlQuery::select); BM25 returns only 2 true SPARQL runners + 8 MediaWiki action-API "
    "queries (different mechanism, graded 0.5 as same Wikimedia-API-query I/O pattern).")

# ===================== CATEGORY D — Domain-specific / niche ==================
# D1 Wikitext internal link extractor (PHP)
BM25["D1"] = [1, 1, 0, 1, 1, 0.5, 0.5, 1, 1, 0.5]
C2C["D1"]  = [0.5, 1, 1, 1, 0.5, 0.5, 0, 0.5, 1, 1]
COMMENTS["D1"] = ("Both strong: discriminative domain tokens (wikitext, preg_match_all, [[, "
    "Title::newFromText). BM25 r3 is a test (0); link add/remove helpers 0.5. C2C (local): "
    "r2 getFilesFromWikiText, r3 extract_links (Rust tree-sitter), r4 "
    "WikitextLinksExtractor::getLinksToNamespace, r9 InternalLinksHelper::parse, r10 "
    "getWeightedLinks are genuine [[...]] internal-link extractors (1); r1 the "
    "WikitextLinksExtractor class 0.5 (container); r5 findLinks (external), r6 "
    "getTemplateTitles ({{..}}), r8 getMentionedUsersFromWikitext 0.5; r7 getItemList "
    "(list items, not links) 0.")

# D2 Git-compatible SHA-1 / SWHID (Python) -- NICHE, both miss specifics
BM25["D2"] = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
C2C["D2"]  = [0.5, 0, 0, 0.5, 0.5, 0.5, 0, 0, 0.5, 0.5]
COMMENTS["D2"] = ("NEITHER finds the git-blob-header/SWHID specifics (likely unique to this "
    "tool's own preprocessing, not in corpus). BM25 returns generic sha1 hexdigest (sha_utf8, "
    "sha1sum). C2C (local): r1 sha256_of, r4 sha1sum, r5/r6 pip rehash, r9 calculate_sha256, "
    "r10 _calculate_sha512 are generic content/file hashers (0.5); r2/r3/r7 are sha1 unit "
    "tests (0) and r8 File.__hash__ returns hash(self.sha1) (0). Strict P@10 = 0 for both.")

# D3 IRC message line parser (Python)
BM25["D3"] = [0, 0.5, 0.5, 0.5, 0, 0.5, 0, 0.5, 0.5, 0]
C2C["D3"]  = [1, 1, 0.5, 0.5, 0.5, 0.5, 1, 0.5, 0.5, 0.5]
COMMENTS["D3"] = ("C2C win. BM25 matched parts/params/split -> generic structured-string "
    "parsers (HTTP accept header, mime-type, CSS prop): no IRC. C2C finds real IRC code from "
    "IRC-bot repos: parsecmd, irc_RPL_NAMREPLY, getNick(hostmask).")

# D4 MediaWiki hook dispatcher (PHP) -- BM25 WIN
BM25["D4"] = [1, 0.5, 0.5, 1, 0.5, 0, 0.5, 0, 0, 0]
C2C["D4"]  = [0, 0, 0.5, 0.5, 0, 0, 0.5, 0, 0, 0]
COMMENTS["D4"] = ("BM25 WIN. BM25 r1 is the EXACT answer (HookContainer::run dispatcher) + the "
    "class; getHandlers/isRegistered 0.5. C2C MISSED HookContainer::run entirely and returned "
    "8 near-duplicate HookRegistryTest::assertThatHookIsExcutable test helpers (graded 0 as tests) "
    "+ isRegistered/echo-callback (0.5). Embedding drifted to hook-adjacent test code.")


def p10_lenient(scores):   # primary metric per manuscript: fraction with score >= 0.5
    return sum(1 for s in scores if s >= 0.5) / 10.0


def p10_strict(scores):    # fully-relevant only: fraction with score == 1.0
    return sum(1 for s in scores if s >= 1.0) / 10.0


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    cats = {"A": [], "B": [], "C": [], "D": []}
    for qid in sorted(BM25, key=lambda q: (q[0], int(q[1:]))):
        if qid not in C2C:
            continue
        cats[qid[0]].append((
            qid,
            p10_lenient(BM25[qid]), p10_lenient(C2C[qid]),
            p10_strict(BM25[qid]), p10_strict(C2C[qid]),
        ))

    hdr = f"{'QID':<5}{'BM25':>7}{'C2C':>7}   {'BM25*':>7}{'C2C*':>7}"
    print(hdr + "   (*=strict, fully-relevant only)")
    print("-" * 46)
    ab, ac, sb, sc = [], [], [], []
    for cat in ["A", "B", "C", "D"]:
        for qid, bl, cl, bs, cs in cats[cat]:
            print(f"{qid:<5}{bl:>7.1f}{cl:>7.1f}   {bs:>7.1f}{cs:>7.1f}")
            ab.append(bl); ac.append(cl); sb.append(bs); sc.append(cs)
        n = len(cats[cat])
        mbl = sum(x[1] for x in cats[cat]) / n
        mcl = sum(x[2] for x in cats[cat]) / n
        mbs = sum(x[3] for x in cats[cat]) / n
        mcs = sum(x[4] for x in cats[cat]) / n
        print(f"  Cat {cat} mean (n={n}): BM25={mbl:.2f} C2C={mcl:.2f}   "
              f"strict BM25={mbs:.2f} C2C={mcs:.2f}")
        print("-" * 46)
    n = len(ab)
    print(f"OVERALL (n={n}): BM25={sum(ab)/n:.3f}  C2C={sum(ac)/n:.3f}")
    print(f"OVERALL strict : BM25={sum(sb)/n:.3f}  C2C={sum(sc)/n:.3f}")

    out = {"metric": "P@10 = fraction of top-10 with graded relevance >= 0.5 (primary); "
                      "strict = fraction == 1.0",
           "judge": "Claude Opus 4.8 (single adjudicator, pooled BM25+Code2Code top-10)",
           "per_query": {q: {"bm25_scores": BM25[q], "c2c_scores": C2C[q],
                             "bm25_p10": p10_lenient(BM25[q]), "c2c_p10": p10_lenient(C2C[q]),
                             "bm25_p10_strict": p10_strict(BM25[q]),
                             "c2c_p10_strict": p10_strict(C2C[q]),
                             "comment": COMMENTS.get(q, "")}
                         for q in BM25 if q in C2C}}
    with open(os.path.join(here, "judge_annotations.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
