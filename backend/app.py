from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Initialise singletons
bi_model = None
rerank_model = None
rerank_tokenizer = None
index = None
metadata = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bi_model, rerank_model, rerank_tokenizer, index, metadata
    
    print("Initialising Jina Code Embeddings (Recall model)...")
    # Bi-Encoder (Recall)
    bi_model = SentenceTransformer("jinaai/jina-code-embeddings-0.5b", trust_remote_code=True, device="cpu")
    
    print("Initialising Jina Reranker v2 (Rerank model)...")
    # Cross-Encoder (Rerank)
    # Using float32 for CPU base, as bitsandbytes (int8) is CUDA only.
    # To truly scale on Toolforge, we'd use Optimum/OpenVINO or Torch Dynamic Quantization.
    rerank_model = AutoModelForSequenceClassification.from_pretrained(
        "jinaai/jina-reranker-v2-base-multilingual", 
        trust_remote_code=True,
        torch_dtype=torch.float32 # Jina v2 code expects torch_dtype despite transformers warning
    ).to("cpu")
    rerank_model.eval()
    rerank_tokenizer = AutoTokenizer.from_pretrained("jinaai/jina-reranker-v2-base-multilingual")
    
    # Apply dynamic quantization to Reranker for CPU memory savings
    # (Reduces RAM footprint significantly for Toolforge)
    print("Applying dynamic quantization to Reranker...")
    rerank_model = torch.quantization.quantize_dynamic(
        rerank_model, {torch.nn.Linear}, dtype=torch.qint8
    )

    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(METADATA_PATH):
        print("Loading FAISS index and metadata...")
        index = faiss.read_index(FAISS_INDEX_PATH)
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        print("⚠️ Warning: Index or metadata not found. Please run build.py first.")
    
    yield
    # Cleanup logic can go here

app = FastAPI(title="Event Horizon: Semantic Code Search", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FAISS_INDEX_PATH = "event_horizon.index"
METADATA_PATH = "functions.json"



class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

@app.post("/search")
def search_code(req: SearchQuery):
    if bi_model is None or index is None or rerank_model is None:
        return {"error": "Server not fully initialised or index missing"}

    # 1. RECALL PHASE: Bi-Encoder + FAISS
    # Task instruction prefix recommended by Jina
    instruction = "Find the most relevant code snippet given the following query:\n"
    xq = bi_model.encode([instruction + req.query], normalize_embeddings=True)
    xq = np.array(xq).astype('float32')

    # Retrieve top candidates for reranking
    # We retrieve more than req.top_k to allow the reranker to find better candidates
    recall_k = max(50, req.top_k * 2) 
    distances, indices = index.search(xq, recall_k)

    candidates = []
    for i, idx in enumerate(indices[0]):
        if idx != -1 and idx < len(metadata):
            item = metadata[idx]
            # Convert L2 distance to confidence
            dist = float(distances[0][i])
            recall_score = 1.0 / (1.0 + dist)
            candidates.append({**item, "recall_score": recall_score})

    if not candidates:
        return {"results": []}

    # 2. RERANK PHASE: Cross-Encoder (Jina Reranker v2)
    # Prepare pairs: (query, code_snippet)
    pairs = [[req.query, c["code"]] for c in candidates]
    
    with torch.no_grad():
        inputs = rerank_tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512)
        # Note: Dynamic quantized model is used here
        scores = rerank_model(**inputs).logits.squeeze().tolist()
        
    # Standardize result scores (usually logits for rerankers)
    if isinstance(scores, float): scores = [scores] # handle single result case
    
    for i, score in enumerate(scores):
        candidates[i]["rerank_score"] = score

    # Sort by rerank score
    candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

    # 3. FORMAT RESULTS
    final_results = []
    for item in candidates[:req.top_k]:
        final_results.append({
            "recall_score": item["recall_score"],
            "rerank_score": item["rerank_score"],
            "swhid": item.get("swhid"),
            "name": item.get("name"),
            "filepath": item.get("filepath"),
            "code": item.get("code")
        })
    
    return {"results": final_results}

# Mount the static frontend directory
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.get("/health")
def health():
    return {"status": "ok", "index_size": index.ntotal if index else 0}

