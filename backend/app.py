from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import faiss
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer

app = FastAPI(title="Event Horizon: Semantic Code Search")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FAISS_INDEX_PATH = "event_horizon.index"
METADATA_PATH = "functions.json"

# Initialize singletons
model = None
index = None
metadata = []

@app.on_event("startup")
def startup_event():
    global model, index, metadata
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(METADATA_PATH):
        print("Loading FAISS index and metadata...")
        index = faiss.read_index(FAISS_INDEX_PATH)
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        print("⚠️ Warning: Index or metadata not found. Please run build.py first.")

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

@app.post("/search")
def search_code(req: SearchQuery):
    if model is None or index is None:
        return {"error": "Server not fully initialized or index missing"}

    # Embed query
    xq = model.encode([req.query]).astype('float32')

    # Search in FAISS
    distances, indices = index.search(xq, req.top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1 and idx < len(metadata):
            item = metadata[idx]
            # Convert L2 distance to confidence (0-1 range roughly)
            # Heuristic: 1 / (1 + dist)
            dist = float(distances[0][i])
            confidence = 1.0 / (1.0 + dist)
            
            results.append({
                "score": confidence,
                "swhid": item.get("swhid"),
                "name": item.get("name"),
                "filepath": item.get("filepath"),
                "code": item.get("code")
            })
    
    # Sort by decreasing confidence (most relevant first)
    results.sort(key=lambda x: x["score"], reverse=True)
    return {"results": results}

    return {"results": results}

# Mount the static frontend directory
# Note: In a production app, the frontend path might be different
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.get("/health")
def health():
    return {"status": "ok", "index_size": index.ntotal if index else 0}
