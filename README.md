# MediaWiki Code2Code Search

![MediaWiki Code2Code Search Banner](https://img.shields.io/badge/Status-Optimized-success?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20|%20Jina%20|%20FAISS-orange?style=for-the-badge)
![Scaling](https://img.shields.io/badge/Index-2400+%20Repos-bluev?style=for-the-badge)

A multi-stage, high-precision semantic code search engine designed for the MediaWiki ecosystem. 
Built on a hybrid architecture of deep neural retrieval (Jina 0.5b) and cross-encoder re-ranking (Jina Reranker v3), 
optimized for large-scale codebases like MediaWiki Core, Extensions, and WMF Operations.

## ✨ Key Features

- **📂 Global MediaWiki Indexing**: Covers Core, Extensions, Skins, Libraries, Services, and more (2,400+ unique repos).
- **🧠 Dual-Phase Retrieval**: 
    - **Recall stage**: Uses `jina-code-embeddings-0.5b` with FAISS `IndexIVFPQ` for fast identification.
    - **Rerank stage**: Uses `jina-reranker-v3` (State-of-the-art) for high-precision ranking.
- **🌳 Granular Structural Filtering**: High-precision extraction and filtering of **Functions**, **Types**, **Template Functions**, and **Template Types** across 10 languages.
- **🏗️ Split-Build Architecture**: Optimized for asymmetric hardware—run heavy extraction on a laptop and neural vectorization on a GPU.
- **🌍 Massive Localization Footprint**: Fully localized UI supporting **17 languages** (Indic, French, Italian, and English).
- **🌌 Octahedron Vortex UI**: A visually stunning frontend built with React and Three.js.

## 🚀 Scaling & Pipeline

The indexing pipeline is designed for a **mass-scale, distributed build**. 

## 🛠️ Setup
Install the necessary dependencies in your virtual environment:
```bash
pip install -r backend/requirements.txt
```

### Phase 1: Discovery & Mirroring (Local)
First, discover the ecosystem and mirror it for processing:
```bash
cd preprocessing
python list_repos.py      # Fetches ~2,500 repo URLs from Hound API
python download_repos.py  # Shallow clones (approx. 70-100GB disk space)
```

### Phase 2: Archiving (Global)
Ensure all repositories are archived in Software Heritage for on-demand retrieval:
```bash
# Requires swh_token in config.json
python archive_to_swh.py
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

### Phase 5: Deployment (Local/Toolforge)
Once the index is built, start the FastAPI backend:
```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000
```
The server will be available at `http://localhost:8000`. You can access the automatic API documentation at `http://localhost:8000/docs`.

---

## 🛠️ Technology Stack

- **Recall Model**: [Jina Code Embeddings (0.5b)](https://huggingface.co/jinaai/jina-code-embeddings-0.5b)
- **Rerank Model**: [Jina Reranker v3](https://huggingface.co/jinaai/jina-reranker-v3)
- **Vector Engine**: [FAISS](https://github.com/facebookresearch/faiss) (IndexIVFPQ for memory efficiency)
- **Segmentation**: [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- **Archive Access**: [Software Heritage S3](https://archive.softwareheritage.org/)
- **Frontend**: React 18 / Three.js

## 📄 License
Apache 2.0 License. Created for advanced code-to-code retrieval within the Wikimedia developer ecosystem.
