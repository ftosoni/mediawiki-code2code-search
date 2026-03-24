# Event Horizon | Semantic Code Search

![Event Horizon Banner](https://img.shields.io/badge/Status-Prototype-orange?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20|%20React%20|%20Three.js-purple?style=for-the-badge)

Event Horizon is a next-generation, high-fidelity code-to-code search engine specifically optimized for the **Software Heritage (SWH)** ecosystem. It allows searching for functionally similar code snippets across large repositories using modern neural retrieval techniques.

## ✨ Key Features

- **🎯 Function-Level Precision**: Unlike traditional file-based search, Event Horizon indexes individual functions, isolating logic from boilerplate and headers.
- **🧠 LLM-Assisted Offsets**: Uses GPT-4o during the build phase to identify exact function boundaries (including docstrings and comments) for language-agnostic precision.
- **🆔 Verified SWHIDs**: Implementation follows strict `swh.model` identification logic, normalization (LF), and canonical hashing to ensure generated identifiers match the Software Heritage archive perfectly.
- **🌌 Octahedron Vortex UI**: A visually stunning search interface built with React and Three.js, featuring a custom particle physics engine and a sleek orange-to-purple technological aesthetic.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API Key (for the indexing pipeline)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/ftosoni/code-search-engine.git
   cd code-search-engine/backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   ```powershell
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Pipeline
To build the index from the base repository (`CoCo-trie`):
1. Set your OpenAI API key in `build.py` or as an environment variable.
2. Run the build script:
   ```bash
   python build.py
   ```
This will generate `functions.json` (metadata) and `event_horizon.index` (vector database).

### Starting the Search Engine
Launch the FastAPI server:
```bash
cd backend
python -m uvicorn app:app --reload
```
Navigate to **`http://127.0.0.1:8000`** in your browser to start exploring the Event Horizon.

## 🛠️ Technology Stack
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Vector Engine**: [FAISS](https://github.com/facebookresearch/faiss)
- **Embeddings**: `all-MiniLM-L6-v2` (Sentence-Transformers)
- **Frontend**: React 18 / Three.js (Single-file weightless implementation)
- **SWH ID Gen**: `swh.model` (Software Heritage identification logic)

## 📄 License
Apache 2.0 License. Created as a prototype for advanced code-to-code retrieval.
