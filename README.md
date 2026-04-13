# MediaWiki Code2Code Search

[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/ftosoni/mediawiki-code2code-search/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/ftosoni/mediawiki-code2code-search)
[![SWH](https://archive.softwareheritage.org/badge/swh:1:dir:f2e3873c00b929f3c0af674ea4d978be92a289ee/)](https://archive.softwareheritage.org/swh:1:dir:f2e3873c00b929f3c0af674ea4d978be92a289ee;origin=https://github.com/ftosoni/mediawiki-code2code-search;visit=swh:1:snp:a9637762b3cd2b31471254da6826c9322e1069f9;anchor=swh:1:rev:0eccd883643a706207d8ff5d10c5954a85b07472)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg?style=flat-square)](https://www.python.org/)
[![CI](https://github.com/ftosoni/mediawiki-code2code-search/actions/workflows/python-ci.yml/badge.svg?branch=main&style=flat-square)](https://github.com/ftosoni/mediawiki-code2code-search/actions/workflows/python-ci.yml)
[![Code Style: PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg?style=flat-square)](https://www.python.org/dev/peps/pep-0008/)
[![License](https://img.shields.io/github/license/ftosoni/mediawiki-code2code-search?style=flat-square)](./LICENSE.md)

A high-performance semantic code search engine designed for the MediaWiki ecosystem. 
Built on the Jina 0.5b neural retrieval model, optimized for large-scale codebases like MediaWiki Core, Extensions, and WMF Operations.
Metadata is managed via indexed SQLite for sub-second responses and a low-memory footprint (Toolforge compatible).

## ✨ Key Features

- **📂 Global MediaWiki Indexing**: Covers Core, Extensions, Skins, Libraries, Services, and more (2,400+ unique repos).
- **🧠 Single-Stage Neural Retrieval**: Uses `jina-code-embeddings-0.5b` with FAISS `IndexIVFPQ` for lightning-fast results (approx. 0.3s).
- **🌳 Granular Structural Filtering**: High-precision extraction and filtering of **Functions**, **Types**, **Template Functions**, and **Template Types** across 10 languages.
- **🏗️ Split-Build Architecture**: Optimized for asymmetric hardware—run heavy extraction on a laptop and neural vectorization on a GPU.
- **🌍 Massive Localization Footprint**: Fully localized UI supporting **17 languages**.
- **🌌 Octahedron Vortex UI**: A visually stunning frontend built with React and Three.js.

## 🚀 Scaling & Pipeline

The indexing pipeline is designed for a **mass-scale, distributed build**. 

## 🛠️ Setup

### Backend (Python)
Create and activate a virtual environment (optional but recommended), then install dependencies:
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### Frontend (Node.js)
To compile the React application, you will need Node.js installed on your machine. Install the dependencies and run the build:
```bash
npm install # This also runs 'npm run build' automatically
```
This generates the pre-compiled `frontend/js/app.js` used by the application.

### Phase 1: Discovery & Mirroring (Local)
First, discover the ecosystem and mirror it for processing:
```bash
cd preprocessing
python list_repos.py      # Fetches 2,400+ repo URLs
python download_repos.py  # Shallow clones (approx. 8GB disk space)
```

### Phase 2: Archiving (Global)
Ensure all repositories are archived in Software Heritage for on-demand retrieval.

> [!NOTE]
> `archive_to_swh.py` requires a "bulk_save" token. For most users, it is recommended to use:
```bash
python archive_individual_to_swh.py
```

### Phase 3: Extraction (Local/CPU)
Perform high-precision structural parsing on your local machine. This captures functions/types with qualified names (e.g., `Class::Method`) and handles complex language features.

**Phase 3a: Structural Extraction**
```bash
python extract_structural_entities.py
```

**Phase 3b: Identity Resolution**
Resolve Git-compatible hashes to standard SHA1. You can do this either locally (fast) or via the Software Heritage API (official):

*   **Option A: Local Resolution (Recommended)**
    ```bash
    python resolve_swh_hashes_local.py
    ```
*   **Option B: API-based Resolution**
    ```bash
    python resolve_swh_hashes.py
    ```

### Phase 4: Indexing (Remote/GPU)
Move `raw_functions.json` to a GPU-equipped environment to compute neural vectors and build the FAISS index.
```bash
cd backend
python generate_index.py  # Auto-detects CUDA/GPU
```

### Phase 5: Memory Optimization & Deployment (Local/Toolforge)
Before deploying, convert the production metadata to SQLite to stay within 6GiB RAM limits:
```bash
cd backend
python migrate_to_sqlite.py
```

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
scp -r "./models" supnabla@login.toolforge.org:/data/project/code2codesearch/
scp -r "./backend/mediawiki.index" supnabla@login.toolforge.org:/data/project/code2codesearch/backend/
scp -r "./backend/functions.db" supnabla@login.toolforge.org:/data/project/code2codesearch/backend/
```

### 2. Configure Permissions
Log into Toolforge and set the necessary permissions:

```bash
ssh supnabla@login.toolforge.org

chmod -R a+r /data/project/code2codesearch/mediawiki-code2code-search/models/
chmod a+x /data/project/code2codesearch/backend/functions.db
chmod a+x /data/project/code2codesearch/backend/mediawiki.index
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

---

## 🛠️ Technology Stack

- **Neural Model**: [Jina Code Embeddings (0.5b)](https://huggingface.co/jinaai/jina-code-embeddings-0.5b)
- **Vector Engine**: [FAISS](https://github.com/facebookresearch/faiss) (IndexIVFPQ for memory efficiency)
- **Segmentation**: [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- **Archive Access**: [Software Heritage](https://archive.softwareheritage.org/)
- **Frontend**: React 18 / Three.js


## 📄 Licence
[Apache 2.0 License](./LICENSE.md). Created for advanced code-to-code retrieval within the Wikimedia developer ecosystem.
