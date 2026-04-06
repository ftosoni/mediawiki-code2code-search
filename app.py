# This file is part of MediaWiki Code2Code Search
# <https://github.com/ftosoni/mediawiki-code2code-search>.
# Copyright (c) 2026 Francesco Tosoni.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import getpass
try:
    import pwd
except ImportError:
    pwd = None

# Patch per Toolforge/Kubernetes - evita getpass.getuser() failures
os.environ.setdefault('TORCHINDUCTOR_CACHE_DIR', '/tmp/torch_cache')
os.environ.setdefault('TORCHDYNAMO_DISABLE', '1')
os.environ.setdefault('TORCH_COMPILE_DISABLE', '1')
os.environ.setdefault('TQDM_DISABLE', '1') # Disables progress bars that break logs
os.environ.setdefault('TRANSFORMERS_VERBOSITY', 'error') # Reduces noise
os.makedirs('/tmp/torch_cache', exist_ok=True)

# Monkey patch getpass.getuser per Toolforge
original_getuser = getpass.getuser

def patched_getuser():
    try:
        return original_getuser()
    except KeyError:
        # In Toolforge container, uid non esiste in /etc/passwd
        return 'toolforge_user'

getpass.getuser = patched_getuser

from fastapi import FastAPI
from typing import Optional
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import torch
from transformers import AutoModel, AutoTokenizer
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import os
import httpx
import functools
import re
import gzip
import asyncio
import shutil
import time
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Standardise Paths (Script Relative)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "backend", "mediawiki.index")
METADATA_PATH = os.path.join(BASE_DIR, "backend", "functions.json")
CACHE_DIR = os.path.join(BASE_DIR, "backend", "swh_cache")
MODELS_DIR = os.path.join(BASE_DIR, "models")
CACHE_LIMIT_MB = 100

# Debug from here
print("="*50)
print("DEBUGGING PATHS")
print(f"BASE_DIR: {BASE_DIR}")
print(f"MODELS_DIR (relative to app.py): {MODELS_DIR}")
print(f"Current working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')[:10]}")
print(f"Does MODELS_DIR exist? {os.path.exists(MODELS_DIR)}")
if os.path.exists(MODELS_DIR):
    print(f"Contents of MODELS_DIR: {os.listdir(MODELS_DIR)}")
    
# Try standardized abs path
standardized_path = "/data/project/code2codesearch/models"
print(f"Does standardized path exist? {os.path.exists(standardized_path)}")
if os.path.exists(standardized_path):
    print(f"Contents of standardized path: {os.listdir(standardized_path)}")
print("="*50)
# end debug

# Ensure Cache Directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialise singletons
bi_model = None
rerank_model = None
rerank_tokenizer = None
index = None
metadata = []
http_client = None # Async client for SWH API/S3

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bi_model, rerank_model, rerank_tokenizer, index, metadata, http_client
    
    # Init Async HTTP Client
    http_client = httpx.AsyncClient(timeout=10.0)
    
    try:
        print("Initialising Jina Code Embeddings (Recall model)...")
        bi_id = "jinaai/jina-code-embeddings-0.5b"
        bi_local_path = os.path.join(MODELS_DIR, "jina-embeddings")
        
        try:
            if os.path.exists(bi_local_path):
                print(f"Loading Bi-Encoder from local cache: {bi_local_path}")
                bi_model = SentenceTransformer(bi_local_path, trust_remote_code=True, device="cpu")
            else:
                raise FileNotFoundError(f"Local Bi-Encoder path missing: {bi_local_path}")
        except Exception as e:
            print(f"⚠️ Local Bi-Encoder failed ({e}). Falling back to Hugging Face Hub...")
            bi_model = SentenceTransformer(bi_id, trust_remote_code=True, device="cpu")
        
        print("Initialising Jina Reranker v3 (Rerank model)...")
        rerank_id = "jinaai/jina-reranker-v3"
        rerank_local_path = os.path.join(MODELS_DIR, "jina-reranker")
        
        try:
            if os.path.exists(rerank_local_path):
                print(f"Loading Reranker from local cache: {rerank_local_path}")
                rerank_model = AutoModel.from_pretrained(
                    rerank_local_path, 
                    trust_remote_code=True,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True
                ).to("cpu")
                rerank_tokenizer = AutoTokenizer.from_pretrained(rerank_local_path, trust_remote_code=True)
            else:
                raise FileNotFoundError(f"Local Reranker path missing: {rerank_local_path}")
        except Exception as e:
            print(f"⚠️ Local Reranker failed ({e}). Falling back to Hugging Face Hub...")
            rerank_model = AutoModel.from_pretrained(
                rerank_id, 
                trust_remote_code=True,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            ).to("cpu")
            rerank_tokenizer = AutoTokenizer.from_pretrained(rerank_id, trust_remote_code=True)
        
        rerank_model.eval()
        
        # Apply dynamic quantization to Reranker for CPU memory savings
        # (Reduces RAM footprint significantly for Toolforge)
        print("Applying dynamic quantization to Reranker...")
        rerank_model = torch.quantization.quantize_dynamic(
            rerank_model, {torch.nn.Linear}, dtype=torch.qint8
        )

        if not os.path.exists(FAISS_INDEX_PATH):
            print(f"⚠️ Warning: FAISS Index not found at {FAISS_INDEX_PATH}. Please run build.py first.")
        elif not os.path.exists(METADATA_PATH):
            print(f"⚠️ Warning: Metadata not found at {METADATA_PATH}. Please run build.py first.")
        else:
            print(f"Loading FAISS index from {FAISS_INDEX_PATH}...")
            index = faiss.read_index(FAISS_INDEX_PATH)
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            print(f"Index loaded. Metadata entries: {len(metadata)}")
    except Exception as e:
        print(f"❌ CRITICAL ERROR DURING LIFESPAN INITIALIZATION: {e}")
        # Allow the app to start even if models fail, for diagnostics
    
    yield
    # Cleanup
    if http_client:
        await http_client.aclose()

class SWHS3Cache:
    """Bounded Disk LRU Cache for Gzipped blobs from SWH S3"""
    
    @staticmethod
    def get_path(content_hash: str):
        return os.path.join(CACHE_DIR, f"{content_hash}.gz")

    @staticmethod
    def prune():
        """Ensure cache stays under CACHE_LIMIT_MB by deleting oldest files"""
        files = []
        total_size = 0
        for f in Path(CACHE_DIR).glob("*.gz"):
            stat = f.stat()
            files.append((stat.st_atime, stat.st_size, f))
            total_size += stat.st_size
        
        limit_bytes = CACHE_LIMIT_MB * 1024 * 1024
        if total_size <= limit_bytes:
            return

        # Sort by access time (oldest first)
        files.sort()
        for _, size, path in files:
            if total_size <= limit_bytes:
                break
            try:
                os.remove(path)
                total_size -= size
                print(f"Pruned cache item: {path.name}")
            except Exception:
                pass

    @staticmethod
    async def fetch_blob(sha1: str):
        """Tiered Fetch Strategy: Local Disk Cache -> SWH S3"""
        if not sha1:
            return None
            
        cache_path = SWHS3Cache.get_path(sha1)
        
        # 1. Check Disk Cache
        if os.path.exists(cache_path):
            os.utime(cache_path, None)
            try:
                with gzip.open(cache_path, "rb") as f:
                    return f.read().decode('utf-8', errors='replace')
            except Exception as e:
                print(f"Cache Read Error for {sha1}: {e}")
                os.remove(cache_path)

        # 2. Try S3 (Primary Remote) - Gzipped blob
        s3_url = f"https://softwareheritage.s3.amazonaws.com/content/{sha1}"
        try:
            response = await http_client.get(s3_url)
            if response.status_code == 200:
                SWHS3Cache.prune()
                # Store the gzipped blob locally
                with open(cache_path, "wb") as f:
                    f.write(response.content)
                # Decompress for use
                decompressed = gzip.decompress(response.content)
                return decompressed.decode('utf-8', errors='replace')
            else:
                print(f"SWH S3 404 for {sha1}")
        except Exception as e:
            print(f"SWH S3 Error for {sha1}: {e}")
        
        return None

app = FastAPI(title="MediaWiki Code2Code Search", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    repo_group: Optional[str] = "all"
    type_filter: str = "all" # all, function, type, template_function, template_type

# Legacy helper removed. Use SWHS3Cache.fetch_blob()

@app.get("/code")
async def get_code_snippet(swhid: str):
    # 1. Extract content hash (legacy fallback if needed, but we prefer sha1)
    hash_match = re.search(r"swh:1:cnt:([0-9a-f]+)", swhid)
    if not hash_match:
        return {"error": "Invalid SWHID format"}
    swhid_hash = hash_match.group(1)

    # 2. Look up sha1 in metadata
    sha1 = None
    for item in metadata:
        if swhid_hash in item.get("swhid", ""):
            sha1 = item.get("sha1")
            break
            
    if not sha1:
        return {"error": "SWHID not found in index metadata"}

    # 3. Extract line range
    line_match = re.search(r"lines=(\d+)-(\d+)", swhid)
    if not line_match:
        return {"error": "Line range missing in SWHID"}
    start_line = int(line_match.group(1))
    end_line = int(line_match.group(2))

    # 4. Fetch full content from Bounded Cache using standard sha1
    full_content = await SWHS3Cache.fetch_blob(sha1)
    if not full_content:
        return {"error": "Could not retrieve content from SWH Archive"}

    # 5. Slice lines
    lines = full_content.splitlines()
    snippet = "\n".join(lines[start_line-1 : end_line])
    return {"code": snippet}

@app.post("/search")
async def search_code(req: SearchRequest):
    if bi_model is None or index is None or rerank_model is None:
        return {"error": "Server not fully initialised"}

    # 1. RECALL PHASE (Bi-Encoder)
    instruction = "Find the most relevant code snippet given the following query:\n"
    xq = bi_model.encode([instruction + req.query], normalize_embeddings=True)
    query_vec = np.array(xq).astype('float32')

    # Retrieve 50 candidates regardless of top_k to ensure quality for rerank
    RECALL_K = 50
    distances, indices = index.search(query_vec, RECALL_K)
    top_indices = indices[0]
    
    # Get metadata and filter by group/type if specified
    candidates = []
    for i, idx in enumerate(top_indices):
        if idx != -1 and idx < len(metadata):
            item = metadata[int(idx)].copy()
            item["recall_score"] = float(distances[0][i])
            
            # Application of filters
            group_match = (req.repo_group == "all" or item.get("repo_group") == req.repo_group)
            type_match = (req.type_filter == "all" or item.get("type") == req.type_filter)
            
            if group_match and type_match:
                candidates.append(item)
    
    if not candidates:
        return {"results": [], "total": 0}

    # We can rerank up to some reasonable limit (e.g. 50)
    ready_for_rerank_meta = candidates # Re-ranking all candidates that passed filtering

    # 2. BATCH FETCH PHASE (Deduplicated Parallel S3 Access)
    unique_sha1s = {c["sha1"] for c in ready_for_rerank_meta if c.get("sha1")}
    blob_tasks = {s: SWHS3Cache.fetch_blob(s) for s in unique_sha1s}
    blob_map = {}
    
    fetch_results = await asyncio.gather(*blob_tasks.values())
    for (s, content) in zip(blob_tasks.keys(), fetch_results):
        blob_map[s] = content

    # 3. PREPARE FOR RERANK (Local Slicing)
    ready_for_rerank = []
    for cand in ready_for_rerank_meta:
        sha1 = cand.get("sha1")
        l_match = re.search(r"lines=(\d+)-(\d+)", cand["swhid"])
        
        if sha1 and l_match:
            full_text = blob_map.get(sha1)
            if full_text:
                s_l, e_l = int(l_match.group(1)), int(l_match.group(2))
                lines = full_text.splitlines()
                # Populate candidate with actual code for reranker
                cand["code"] = "\n".join(lines[s_l-1 : e_l])
                ready_for_rerank.append(cand)

    if not ready_for_rerank:
        return {"results": []}

    # 4. RERANK PHASE (Cross-Encoder)
    rerank_results = rerank_model.rerank(
        query=req.query, 
        documents=[c["code"] for c in ready_for_rerank], 
        top_n=req.top_k,
        max_doc_length=512
    )

    final_results = []
    for res in rerank_results:
        cand = ready_for_rerank[res['index']]
        cand["rerank_score"] = float(res['relevance_score'])
        final_results.append(cand)

    return {"results": final_results}

@app.get("/health")
def health():
    return {"status": "ok", "index_size": index.ntotal if index else 0}

# Mount the static frontend directory last to avoid intercepting API calls
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend"))
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
