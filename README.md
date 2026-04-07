# MediaWiki Code2Code Search

![MediaWiki Code2Code Search Banner](https://img.shields.io/badge/Status-Optimized-success?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20|%20Jina%20|%20FAISS-orange?style=for-the-badge)
![Scaling](https://img.shields.io/badge/Index-2400+%20Repos-bluev?style=for-the-badge)

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
Create and activate a virtual environment (optional but recommended), then install dependencies:
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

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
Perform structural parsing on your local laptop. This captures functions/types and generates `raw_functions.json`.
```bash
python extract_entities.py
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
python backend/migrate_to_sqlite.py
```

Once the index and database are ready, start the FastAPI backend from the root directory:
```bash
# From the project root
uvicorn app:app --host 0.0.0.0 --port 8000
```
The server will be available at `http://localhost:8000`. You can access the automatic API documentation at `http://localhost:8000/docs`.


---

## 🛠️ Technology Stack

- **Neural Model**: [Jina Code Embeddings (0.5b)](https://huggingface.co/jinaai/jina-code-embeddings-0.5b)
- **Vector Engine**: [FAISS](https://github.com/facebookresearch/faiss) (IndexIVFPQ for memory efficiency)
- **Segmentation**: [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- **Archive Access**: [Software Heritage S3](https://archive.softwareheritage.org/)
- **Frontend**: React 18 / Three.js


## 📄 License
Apache 2.0 License. Created for advanced code-to-code retrieval within the Wikimedia developer ecosystem.
