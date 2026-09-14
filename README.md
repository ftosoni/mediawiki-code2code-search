# MediaWiki Code2Code Search

A high-performance semantic code search engine designed for the MediaWiki ecosystem. 
Built on the Qwen 0.6B neural retrieval model, optimized for large-scale codebases like MediaWiki Core, Extensions, and WMF Operations.
Metadata is managed via indexed SQLite for sub-second responses and a low-memory footprint (Toolforge compatible).

As featured on [Wikimedia Diff](https://diff.wikimedia.org/2026/04/14/introducing-mediawiki-code2code-search-semantic-search-to-find-code-by-under-the-surface-similarity/) (v1.0.0).

## ✨ Key Features

- **📂 Global MediaWiki Indexing**: Covers Core, Extensions, Skins, Libraries, Services, and more (2,500+ unique repos).
- **🧠 Single-Stage Neural Retrieval**: Uses `Qwen3-Embedding-0.6B` with FAISS `IndexIVFPQ` for lightning-fast results (approx. 0.3s).
- **🌳 Granular Structural Filtering**: High-precision extraction and filtering of **Functions**, **Types**, **Template Functions**, and **Template Types** across 10 languages.
- **🏗️ Split-Build Architecture**: Optimized for asymmetric hardware—run heavy extraction on a laptop and neural vectorization on a GPU.
- **🌍 Massive Localization Footprint**: Fully localized UI supporting **17 languages**.
- **🎨 Codex UI**: A clean, accessible frontend built with Wikimedia's **Codex Design System** for a native look and feel.
- **🔍 Advanced Multi-select Filtering**: Granular control over results by repository group, programming language, and entry type.

## 📂 Project Structure

```
mediawiki-code2code-search/
├── frontend/                  # Codex-based Static Frontend
│   ├── css/style.css          # Stylesheets using the Codex Design System
│   ├── js/main.js             # Main frontend application logic
│   └── i18n/                  # Localization JSONs supporting 17 languages
├── backend/                   # FAISS Index, SQLite & Vector DB Management
│   ├── generate_embeddings.py # Computes neural embeddings from raw snippets (saves embeddings.npy)
│   ├── build_index.py         # Trains and builds the FAISS search index from saved embeddings
│   ├── migrate_to_sqlite.py   # RAM optimization script (JSON metadata -> SQLite)
│   ├── snippets.db            # SQLite metadata store for fast lookups
│   └── mediawiki.index        # Compiled FAISS vector index
├── preprocessing/             # Global-Scale Indexing Pipeline (Phases 1-4)
│   ├── list_repos.py          # Discovers and lists 2,500+ MediaWiki repositories
│   ├── download_repos.py      # Handles shallow clones of target repositories
│   ├── extract_entities.py    # Structural parsing & AST entity extraction
│   ├── archive_to_swh.py      # Software Heritage archiving pipeline scripts
│   └── resolve_swh_hashes.py  # Resolves local Git hashes to SWH SHA1 IDs
├── tests/                     # Parser & API Verification Suite
│   ├── test_api.py            # Backend API endpoint tests
│   ├── test_*_parser.py       # Syntax extraction validations for 10+ languages
│   └── example.*              # Target language snippets parsed during testing
├── scripts/                   # Internal utilities & metadata migration helpers
├── manuscript/                # Academic paper & System documentation (LaTeX)
│   ├── main.tex               # Manuscript source file documenting architecture
│   └── main.pdf               # Compiled system documentation/paper
├── app.py                     # Root FastAPI web application entry point
├── download_models.py         # Script to pre-download model weights locally
├── requirements.txt           # Python backend dependencies
└── CITATION.cff               # CITATION file for academic/repository reference
```

## 🚀 Scaling & Pipeline

The indexing pipeline is designed for a **mass-scale, distributed build**. 

## 📊 Evaluation

We benchmark the semantic retriever against a **BM25 lexical baseline** on a **27-query** suite
(canonical algorithms, name-obfuscated semantics, cross-language, and domain-specific tasks) under a
**blinded LLM-as-a-judge** protocol: both systems' top-10 are pooled, deduplicated by content hash,
shuffled, and graded (1.0 relevant / 0.5 partial / 0.0 irrelevant) by **three independent judges from
different model families** — Claude Opus 4.8, Gemini 3.8 Flash, and Kimi K2. Judges never see system
identity, rank, or filenames; all metrics are computed in Python. Inter-judge reliability is
**Krippendorff's α = 0.74**.

**Headline (jury-mean nDCG@10): `0.81` for Code2Code vs `0.63` for BM25** — a paired improvement of
**+0.18 (95% CI [0.05, 0.32])** that excludes zero under *every* judge. Across the 27 queries,
Code2Code wins **15**, ties **7**, and trails BM25 on **5** (tie band |Δ| < 0.05).

| Category | Queries | Code2Code nDCG@10 | BM25 nDCG@10 |
|---|---|:---:|:---:|
| **A** — Canonical algorithms | 5 | 0.90 | 0.82 |
| **B** — Name-obfuscated semantics | 12 | 0.83 | 0.53 |
| **C** — Cross-language | 6 | 0.81 | 0.62 |
| **D** — Domain-specific / niche | 4 | 0.64 | 0.69 |
| **All** | 27 | **0.81** | **0.63** |

The gain concentrates where lexical matching is weakest (name-obfuscation and cross-language); BM25
stays competitive on niche domain patterns whose queries share discriminative tokens with the target.

<details>
<summary><b>Per-query results (jury-mean nDCG@10, all 27 queries)</b></summary>

| Q | Title | Lang | C2C | BM25 | Δ | Verdict |
|---|---|---|:---:|:---:|:---:|---|
| A1 | Greatest common divisor | Python | 1.00 | 0.89 | +0.11 | 🟢 C2C |
| A2 | Binary search | JavaScript | 0.99 | 0.98 | +0.01 | ⚪ tie |
| A3 | String truncation with ellipsis | PHP | 0.92 | 0.68 | +0.24 | 🟢 C2C |
| A4 | JSON encode with error forwarding | Go | 0.65 | 0.64 | +0.01 | ⚪ tie |
| A5 | Retry with exponential back-off | Python | 0.95 | 0.92 | +0.02 | ⚪ tie |
| B1 | Permission check: canUserEdit | PHP | 0.90 | 0.68 | +0.22 | 🟢 C2C |
| B2 | Debounce: query names it delayExecution | JavaScript | 0.61 | 0.84 | -0.23 | 🔴 BM25 |
| B3 | Session invalidation: invalidateUserSession | PHP | 0.98 | 0.96 | +0.03 | ⚪ tie |
| B4 | LRU eviction: query calls it evictOldest | Python | 0.98 | 0.00 | +0.98 | 🟢 C2C |
| B5 | Rate-limit gate: query says isRateLimited | PHP | 0.94 | 0.29 | +0.65 | 🟢 C2C |
| B6 | Error normaliser: query calls it toError | TypeScript | 0.71 | 0.00 | +0.71 | 🟢 C2C |
| B7 | URL slug: query calls it make_slug | Python | 0.93 | 0.75 | +0.18 | 🟢 C2C |
| B8 | CAPTCHA verify: different field names | PHP | 0.91 | 0.19 | +0.72 | 🟢 C2C |
| B9 | Worker pool: query calls it processWithPool | Go | 0.54 | 0.61 | -0.07 | 🔴 BM25 |
| B10 | Recursive category subtree: getDescendants | PHP | 0.99 | 0.85 | +0.14 | 🟢 C2C |
| B11 | Paginated API fetch: fetch_all_pages | Python | 0.97 | 0.76 | +0.21 | 🟢 C2C |
| B12 | HTTP retry on 5xx: query calls it doWithRetry | Go | 0.51 | 0.46 | +0.05 | ⚪ tie |
| C1 | SHA-256 file hash | PHP → Go / Python | 1.00 | 0.00 | +1.00 | 🟢 C2C |
| C2 | ISO-8601 date parsing | Python → PHP / JS | 1.00 | 0.99 | +0.01 | ⚪ tie |
| C3 | Fan-out / parallel map | Go → JS Promise.all | 0.52 | 0.43 | +0.08 | 🟢 C2C |
| C4 | Throttle / call-rate limiter | TypeScript → PHP | 0.99 | 0.94 | +0.05 | ⚪ tie |
| C5 | Recursive table/dict serialiser | Lua → Python / PHP | 0.42 | 0.89 | -0.47 | 🔴 BM25 |
| C6 | Wikidata SPARQL query runner | Python → PHP / JS | 0.97 | 0.44 | +0.53 | 🟢 C2C |
| D1 | Wikitext internal link extractor | PHP | 0.91 | 0.83 | +0.08 | 🟢 C2C |
| D2 | Git-compatible SHA-1 / SWHID computation | Python | 0.46 | 0.66 | -0.20 | 🔴 BM25 |
| D3 | IRC message line parser | Python | 0.53 | 0.35 | +0.18 | 🟢 C2C |
| D4 | MediaWiki hook dispatcher | PHP | 0.66 | 0.92 | -0.27 | 🔴 BM25 |

</details>

**Reproducibility.** The frozen benchmark, blinded prompts, per-judge relevance labels, and the
analysis code that computes every number above live in [`scripts/evaluation/`](scripts/evaluation/)
(methodology in [`scripts/evaluation/CLAUDE.md`](scripts/evaluation/CLAUDE.md)); regenerate the report
with `python scripts/evaluation/analyze_labels.py`. The underlying corpus and indexes are on
**[Zenodo](https://doi.org/10.5281/zenodo.20586256)** and **[Hugging Face](https://huggingface.co/datasets/ftosoni/mediawiki-code2code-search)**.

## 🛠️ Setup

### 💾 Pre-computed Artefacts (Recommended)

To run the search engine immediately without running the entire indexing pipeline (Phases 1-6) from scratch, you can download our pre-computed database and FAISS index from the **[Zenodo Dataset](https://doi.org/10.5281/zenodo.20586256)**:
1. Download `snippets.db` and `mediawiki.index`.
2. Place both files inside the `backend/` directory of the project.

For the frozen software source code release of the engine, see **[GitHub Release v2.0.0](https://github.com/ftosoni/mediawiki-code2code-search/releases/tag/v2.0.0)**.

### Backend (Python)
Create and activate a virtual environment (optional but recommended), install dependencies, and pre-download the neural models:
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python download_models.py
```

### Frontend (Static Assets)

The frontend is built with vanilla JavaScript and the Codex Design System. It consists of static HTML, CSS, and JS files located in the `frontend/` directory. These files are served directly by the FastAPI backend.

There is no compilation step required for the frontend.

### Phase 1: Discovery & Mirroring (Local)
First, discover the ecosystem and mirror it for processing:
```bash
cd preprocessing
python list_repos.py      # Fetches 2,500+ repo URLs
python download_repos.py  # Shallow clones (approx. 8GB disk space)
```

### Phase 2: Archiving (Global)
Ensure all repositories are archived in Software Heritage for on-demand retrieval.

> [!NOTE]
> `archive_to_swh.py` requires a "bulk_save" token. For most users, it is recommended to use:
```bash
python archive_individual_to_swh.py
```

### Phase 3: Structural Extraction (Local/CPU)
Perform high-precision structural parsing on your local machine. This captures functions/types with qualified names (e.g., `Class::Method`) and handles complex language features.
```bash
python extract_structural_entities.py
```

### Phase 4: Identity Resolution
Resolve Git-compatible hashes to standard SHA1. You can do this either locally (fast) or via the Software Heritage API (official):

*   **Option A: Local Resolution (Recommended)**
    ```bash
    python resolve_swh_hashes_local.py
    ```
*   **Option B: API-based Resolution**
    ```bash
    python resolve_swh_hashes.py
    ```

### Phase 5: Indexing (Remote/GPU)
Move `raw_snippets.json` to a GPU-equipped environment to compute neural vectors and build the FAISS index.
```bash
cd backend
python generate_embeddings.py  # Computes and saves embeddings to embeddings.npy
python build_index.py          # Trains and builds FAISS index from embeddings.npy
```

### Phase 6: Memory Optimization
Before deploying, convert the production metadata to SQLite to stay within 6GiB RAM limits:
```bash
cd backend
python migrate_to_sqlite.py
```

### Phase 7: Runtime / Running the Application
Once the index and database are ready, start the FastAPI backend from the root directory:

```bash
# From the project root
uvicorn app:app --host 0.0.0.0 --port 8000
```
The server will be available at `http://localhost:8000`. You can access the automatic API documentation at `http://localhost:8000/docs`.


---

## 🚀 Deployment (Toolforge)

Follow these steps to deploy the application on Wikimedia Toolforge.

> [!NOTE]
> The examples below use `supnabla` as the username and `code2codesearch` as the project name. Replace these with your own Toolforge credentials where applicable.

### 1. Upload Assets
Since the model weights and indexes are large, they should be uploaded from your local machine to the Toolforge project data directory:

```bash
# From the project root
scp -rp "./models" supnabla@login.toolforge.org:/data/project/code2codesearch/
scp -rp "./backend/mediawiki.index" supnabla@login.toolforge.org:/data/project/code2codesearch/backend/
scp -rp "./backend/snippets.db" supnabla@login.toolforge.org:/data/project/code2codesearch/backend/
```

### 2. Configure Permissions
Log into Toolforge and set the necessary permissions:

```bash
ssh supnabla@login.toolforge.org

chmod -R a+rX /data/project/code2codesearch/models/
chmod a+r /data/project/code2codesearch/backend/snippets.db
chmod a+r /data/project/code2codesearch/backend/mediawiki.index
```

### 3. Deploy
Now you are ready to deploy the webservice:

```bash
# Switch to the code2codesearch project
become code2codesearch

# Stop and clean existing build
toolforge webservice buildservice stop --mount=all
toolforge build clean -y

# Start build from repository
toolforge build start https://github.com/ftosoni/mediawiki-code2code-search

# Start webservice with 6GiB RAM
toolforge webservice buildservice start --mount=all -m 6Gi

# Monitor logs
toolforge webservice logs -f
```

### 4. Continuous Deployment
Steps 1 and 2 are one-off. Step 3 is automated: every push to `main` — including the daily
i18n sync from [translatewiki.org](https://translatewiki.org) — rebuilds the image and restarts the
webservice, but only after the `lint` and `test` jobs pass (see [`.github/workflows/python-ci.yml`](.github/workflows/python-ci.yml)).

Two repository secrets are required (*Settings → Secrets and variables → Actions*):

| Secret | Value |
| --- | --- |
| `TOOLFORGE_USERNAME` | Your Wikimedia developer shell name, e.g. `supnabla` |
| `TOOLFORGE_SSH_KEY` | The **private** key whose public half is in your [Wikitech SSH keys](https://wikitech.wikimedia.org/wiki/Special:Preferences#mw-prefsection-openstack) |

The workflow can also be run by hand from the *Actions* tab (`Run workflow`).

> [!NOTE]
> `toolforge webservice buildservice start` returns as soon as the pod is scheduled, not once
> gunicorn has loaded the models — which takes several minutes. The deploy job therefore polls
> `/health` until it answers, so a green run means the new image is actually serving. Until that
> poll succeeds the site may still be down or serving the previous image.

---

## 🛠️ Technology Stack & Project Status

<p align="left">
  <!-- Project Status & License -->
  <a href="https://github.com/ftosoni/mediawiki-code2code-search/actions/workflows/python-ci.yml"><img src="https://github.com/ftosoni/mediawiki-code2code-search/actions/workflows/python-ci.yml/badge.svg?branch=main&style=flat-square" alt="CI Status"></a>
  <a href="./LICENCE.txt"><img src="https://img.shields.io/badge/license-Apache_2.0-blue?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/dev/peps/pep-0008/"><img src="https://img.shields.io/badge/code%20style-pep8-orange.svg?style=flat-square" alt="Code Style: PEP8"></a>
  <a href="https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/ftosoni/mediawiki-code2code-search"><img src="https://archive.softwareheritage.org/badge/origin/https://github.com/ftosoni/mediawiki-code2code-search/" alt="SWH Origin"></a>
  <a href="https://archive.softwareheritage.org/swh:1:dir:fe86b58fb35118c474fce8f7a38b4bc541440653;origin=https://github.com/ftosoni/mediawiki-code2code-search;visit=swh:1:snp:0925f0ac8b48e9b46b741090d50781140d1e037b;anchor=swh:1:rev:fcfcb6a6bff6534ce0a7203d1553219b5947504a"><img src="https://archive.softwareheritage.org/badge/swh:1:dir:c30104117db9bb6a8e488e698173fa2b302cbffc/" alt="SWH Directory"></a>
</p>

<p align="left">
  <!-- Frontend & Design -->
  <a href="https://doc.wikimedia.org/codex/main/"><img src="https://img.shields.io/badge/Codex-Design_System-3366cc?logo=wikimedia-commons&logoColor=white" alt="Codex"></a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript"><img src="https://img.shields.io/badge/JavaScript-ES6+-f7df1e?logo=javascript&logoColor=black" alt="JavaScript"></a>
</p>

<p align="left">
  <!-- Backend & Core -->
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="https://www.uvicorn.org/"><img src="https://img.shields.io/badge/Uvicorn-222?logo=gunicorn&logoColor=white" alt="Uvicorn"></a>
</p>

<p align="left">
  <!-- Vector Search & DB -->
  <a href="https://github.com/facebookresearch/faiss"><img src="https://img.shields.io/badge/FAISS-Vector_Index-blueviolet" alt="FAISS"></a>
  <img src="https://img.shields.io/badge/Vector_Indexes-1024d-blueviolet" alt="Vector indexes (1024d)">
  <a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/SQLite-metadata_store-003b57?logo=sqlite&logoColor=white" alt="SQLite"></a>
</p>

<p align="left">
  <!-- AI, Extraction & Archive -->
  <a href="https://huggingface.co/Qwen/Qwen3-Embedding-0.6B"><img src="https://img.shields.io/badge/Qwen3_Embedding-0.6B-5374ff?logo=huggingface&logoColor=white" alt="Qwen3 Embedding 0.6B"></a>
  <a href="https://tree-sitter.github.io/tree-sitter/"><img src="https://img.shields.io/badge/Tree--sitter-parsers-green" alt="Tree-sitter"></a>
  <a href="https://archive.softwareheritage.org/"><img src="https://img.shields.io/badge/Software_Heritage-archive-002f56" alt="Software Heritage"></a>
</p>

<p align="left">
  <!-- CI/CD & Deploy -->
  <a href="https://wikitech.wikimedia.org/wiki/Portal:Toolforge"><img src="https://img.shields.io/badge/Toolforge-deploy-3366cc" alt="Toolforge"></a>
  <a href="https://github.com/ftosoni/mediawiki-code2code-search/actions"><img src="https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?logo=githubactions&logoColor=white" alt="GitHub Actions"></a>
  <a href="https://docs.pytest.org/"><img src="https://img.shields.io/badge/pytest-tests-0A9EDC?logo=pytest&logoColor=white" alt="pytest"></a>
</p>


## 📄 Licence
[Apache 2.0 License](./LICENCE.txt). Created for advanced code-to-code retrieval within the Wikimedia developer ecosystem.
