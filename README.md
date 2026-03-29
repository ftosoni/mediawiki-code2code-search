# MediaWki Code2Code Search

![Event Horizon Banner](https://img.shields.io/badge/Status-Optimized-success?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20|%20Jina%20|%20FAISS-orange?style=for-the-badge)
![Deployment](https://img.shields.io/badge/Platform-Wikimedia%20Toolforge-blue?style=for-the-badge)

**MediaWki Code2Code Search** is a high-performance, multi-language, memory-efficient semantic code search engine indexing MediaWiki open-source code repositories and linking to the **Software Heritage (SWH)** universal code archive. It implements a modern recall-then-rerank architecture optimized based on Jina AI models for the strict resource constraints of **Wikimedia Toolforge**. Its UI is available in a number of Indic languages as well as in English, French and Italian.

## ✨ Key Features

- **🧠 Dual-Phase Retrieval**: 
    - **Recall stage**: Uses `jina-code-embeddings-0.5b` with FAISS `IndexIVFPQ` (int8 quantized) for lightning-fast candidate identification.
    - **Rerank stage**: Uses `jina-reranker-v2-base-multilingual` with dynamic quantization for high-fidelity ranking of retrieved snippets.
- **🌳 Multi-Language AST Segmentation**: Leverages **Tree-sitter** for high-precision extraction of **Functions** and **Types** (Classes, Structs, Interfaces, Enums, Traits) across 10 languages:
    - PHP, Python, JavaScript, TypeScript, Lua, Go, Java, Rust, C, and C++.
- **🔍 Dual-Category Filtering**: Interface allows granular search toggling between *All Entities*, *Functions*, or *Structural Types* for better architectural discovery.
- **☁️ On-Demand S3 Retrieval**: Instead of storing full source code locally, it fetches gzipped blobs directly from the **Software Heritage S3 bucket** using standard SHA1 hashes, minimizing disk and RAM usage.
- **🌍 Global by Design (i18n)**: Fully localized UI supporting over 15 languages, including Indic languages (Bengali, Hindi, Tamil, Telugu, etc.), French, and Italian.
- **🌌 Octahedron Vortex UI**: A visually stunning frontend built with React and Three.js, featuring a custom particle physics engine and a sleek technological aesthetic.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- `git` (for repository cloning)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/ftosoni/code-search-engine.git
   cd code-search-engine
   ```
2. Setup the virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv venv
   # Windows: .\venv\Scripts\Activate.ps1 | Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```

### Running the Pipeline
To build the semantic index from a target repository:
1. Run the build script:
   ```bash
   python build.py
   ```
This will:
- Clone/update the target repository.
- Segment functions and types using Tree-sitter AST.
- Resolve Git hashes to standard SHA1 via the SWH API.
- Generate a disk-ready FAISS index and metadata.

### Starting the Search Engine
Launch the FastAPI server using Uvicorn:
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```
Navigate to **`http://localhost:8000`** to start exploring the Event Horizon.

## 🛠️ Technology Stack

- **Recall Model**: [Jina Code Embeddings (0.5b)](https://huggingface.co/jinaai/jina-code-embeddings-0.5b)
- **Rerank Model**: [Jina Reranker v2 (Multilingual)](https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual)
- **Vector Engine**: [FAISS](https://github.com/facebookresearch/faiss) (with IndexIVFPQ for memory efficiency)
- **Segmentation**: [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) (10 language parsers)
- **Archive Access**: [Software Heritage S3](https://archive.softwareheritage.org/) (SHA1-based gzipped blob retrieval)
- **Frontend**: React 18 / Three.js (Single-file weightless implementation)

## 📄 License
Apache 2.0 License. Created for advanced code-to-code retrieval within the Wikimedia developer ecosystem.
