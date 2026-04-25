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

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional, Union, List, Literal, Annotated
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import sqlite3
import json
import httpx
import functools
import re
import gzip
import asyncio
import shutil
import time
from pathlib import Path
from dotenv import load_dotenv
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.formatters import HtmlFormatter

# Load local environment variables
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Standardise Paths (Script Relative)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "backend", "mediawiki.index")
METADATA_DB_PATH = os.path.join(BASE_DIR, "backend", "functions.db")
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

# Diagnostic: Check model readability before loading
print("--- DIAGNOSTIC: Checking model readability ---")
try:
    if hasattr(os, 'getuid'):
        print(f"Current process UID: {os.getuid()}, GID: {os.getgid()}")
    if os.path.exists(MODELS_DIR):
        print(f"MODELS_DIR resides at: {MODELS_DIR}")
        for sub in ['jina-embeddings', 'jina-reranker']:
            sub_path = os.path.join(MODELS_DIR, sub)
            if os.path.exists(sub_path):
                readable = os.access(sub_path, os.R_OK)
                executable = os.access(sub_path, os.X_OK)
                print(f"Directory {sub}: Readable={readable}, Executable={executable}")
                # Check a sample file
                sample_file = os.path.join(sub_path, "config.json")
                if os.path.exists(sample_file):
                    file_readable = os.access(sample_file, os.R_OK)
                    print(f"  - {sample_file} readable: {file_readable}")
            else:
                print(f"Directory {sub} MISSING from {MODELS_DIR}")
    else:
        print(f"❌ MODELS_DIR {MODELS_DIR} DOES NOT EXIST")
except Exception as diag_e:
    print(f"Diagnostic error: {diag_e}")
print("----------------------------------------------")

# Initialise singletons
bi_model = None
# Jina Reranker v2 is disabled for CPU performance
# rerank_model = None
# rerank_tokenizer = None
index = None
# metadata list removed to save RAM. Use SQLite at METADATA_DB_PATH instead.
http_client = None # Async client for SWH API/S3

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bi_model, index, http_client

    
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
        
# Jina Reranker v2 is disabled to prioritize sub-second search on CPU
        # print("Initialising Jina Reranker v2 (Rerank model)...")
        # rerank_id = "jinaai/jina-reranker-v2-base-multilingual"
        # rerank_local_path = os.path.join(MODELS_DIR, "jina-reranker")
        
        # try:
        #     if os.path.exists(rerank_local_path):
        #         print(f"Loading Reranker from local cache: {rerank_local_path}")
        #         rerank_model = AutoModelForSequenceClassification.from_pretrained(
        #             rerank_local_path, 
        #             trust_remote_code=True,
        #             torch_dtype="auto",
        #             low_cpu_mem_usage=False
        #         ).to("cpu")
        #         rerank_tokenizer = AutoTokenizer.from_pretrained(rerank_local_path, trust_remote_code=True)
        #     else:
        #         raise FileNotFoundError(f"Local Reranker path missing: {rerank_local_path}")
        # except Exception as e:
        #     print(f"⚠️ Local Reranker failed ({e}). Falling back to Hugging Face Hub...")
        #     rerank_model = AutoModelForSequenceClassification.from_pretrained(
        #         rerank_id, 
        #         trust_remote_code=True,
        #         torch_dtype="auto",
        #         low_cpu_mem_usage=False
        #     ).to("cpu")
        #     rerank_tokenizer = AutoTokenizer.from_pretrained(rerank_id, trust_remote_code=True)
        
        # if rerank_model:
        #     rerank_model.eval()

        
        # NOTE: Dynamic quantization is skipped to prioritize the simplest and fastest startup.
        # This requires setting the webservice memory to at least 6GiB (8GiB recommended).


        
        if not os.path.exists(FAISS_INDEX_PATH):
            print(f"⚠️ Warning: FAISS Index not found at {FAISS_INDEX_PATH}. Please run build.py first.")
        elif not os.path.exists(METADATA_DB_PATH):
            print(f"⚠️ Warning: SQLite Metadata not found at {METADATA_DB_PATH}. Please run backend/migrate_to_sqlite.py first.")
        else:
            print(f"Loading FAISS index from {FAISS_INDEX_PATH}...")
            index = faiss.read_index(FAISS_INDEX_PATH)
            print(f"Index loaded. Metadata managed via SQLite: {METADATA_DB_PATH}")
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

app = FastAPI(
    title="MediaWiki Code2Code Search",
    description="""
    AI-powered semantic search for MediaWiki source code. 
    Find functions, types, and templates across the entire MediaWiki ecosystem using neural retrieval.
    
    This API allows you to:
    * Search code snippets using natural language or code examples.
    * Retrieve specific code snippets by their Software Heritage ID (SWHID).
    * Check the system status and index health.
    """,
    version="1.0.0",
    contact={
        "name": "Francesco Tosoni",
        "url": "https://github.com/ftosoni/mediawiki-code2code-search",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    lifespan=lifespan
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom error handler to provide more precise and readable validation messages.
    """
    errors = []
    for error in exc.errors():
        loc = " -> ".join([str(l) for l in error.get("loc", []) if l != "body"])
        msg = error.get("msg")
        inp = error.get("input")
        errors.append({
            "field": loc,
            "message": msg,
            "received_value": inp
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": "One or more fields in your request are invalid.",
            "invalid_fields": errors
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str = Field(..., max_length=2000, description="The natural language or code query to search for.", examples=["def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a"])
    top_k: int = Field(10, gt=0, le=50, description="The number of results to return (range: 1-50).", examples=[10])
    repo_group: List[Literal['all', 'core', 'things', 'libraries', 'deployed', 'operations', 'puppet', 'pywikibot', 'devtools', 'analytics', 'wmcs', 'apps']] = Field(["all"], description="Filter by repository group(s).")
    type_filter: Literal['all', 'function', 'type', 'template'] = Field("all", description="Filter by entry type.")
    language_filter: List[Literal['all', 'Python', 'C++', 'C', 'PHP', 'JavaScript', 'TypeScript', 'Lua', 'Go', 'Java', 'Rust']] = Field(["all"], description="Filter by programming language(s).")

    @field_validator('repo_group', 'language_filter', mode='before')
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "def get_page_content(title):\n    # Fetch content from MediaWiki API\n    params = {'action': 'query', 'prop': 'revisions', 'titles': title}\n    return requests.get(API_URL, params=params).json()",
                "top_k": 5,
                "repo_group": "deployed",
                "type_filter": "function",
                "language_filter": ["Python", "JavaScript"]
            }
        }
    }

class SearchResult(BaseModel):
    id: int = Field(..., examples=[123])
    name: str = Field(..., examples=["validateEmail"])
    type: str = Field(..., examples=["function"])
    filepath: str = Field(..., examples=["includes/utils/Validator.php"])
    repo_name: str = Field(..., examples=["mediawiki/core"])
    repo_group: str = Field(..., examples=["core"])
    swhid: str = Field(..., examples=["swh:1:cnt:00003a1a9720cf32009cbe0c3b47256ef1a020bd;origin=https:/github.com/Open-CSP/FlexForm;lines=82-97/"])
    recall_score: float = Field(..., examples=[0.9854])
    code: Optional[str] = Field(None, description="The raw code snippet.", examples=["function validateEmail($email) { ... }"])
    highlighted_code: Optional[str] = Field(None, examples=["<span class='k'>function</span> ..."])

class SearchResponse(BaseModel):
    results: List[SearchResult]

class CodeSnippetResponse(BaseModel):
    code: str = Field(..., examples=["function validateEmail($email) { ... }"])
    highlighted_code: str = Field(..., examples=["<span class='k'>function</span> <span class='nf'>validateEmail</span>..."])

class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    index_size: int = Field(..., examples=[1103986])

class ValidationErrorDetail(BaseModel):
    field: str = Field(..., description="The name of the invalid field.", examples=["top_k"])
    message: str = Field(..., description="A clear explanation of the error.", examples=["Input should be less than or equal to 50"])
    received_value: Optional[Union[str, int, float, list, dict]] = Field(None, description="The value that was received and failed validation.", examples=[100])

class ValidationErrorResponse(BaseModel):
    error: str = Field("Validation Error", examples=["Validation Error"])
    detail: str = Field(..., description="A summary of the validation failure.", examples=["One or more fields in your request are invalid."])
    invalid_fields: List[ValidationErrorDetail] = Field(..., description="A list of specific field validation failures.")

class CodeValidationErrorResponse(ValidationErrorResponse):
    invalid_fields: List[ValidationErrorDetail] = Field(..., examples=[
        {
            "field": "query -> swhid",
            "message": "Field required",
            "received_value": None
        }
    ])

# Mapping for language filtering based on file extensions
LANGUAGE_EXTENSIONS = {
    "Python": [".py"],
    "C++": [".cpp", ".hpp", ".h", ".cc", ".cxx"],
    "C": [".c"],
    "PHP": [".php", ".inc"],
    "JavaScript": [".js"],
    "TypeScript": [".ts", ".tsx", ".mts", ".cts"],
    "Lua": [".lua"],
    "Go": [".go"],
    "Java": [".java"],
    "Rust": [".rs"]
}

def get_highlighted_code(code: str, filepath: str) -> str:
    """Returns syntax-highlighted HTML for the given code and filepath extension."""
    try:
        lexer = get_lexer_for_filename(filepath)
    except Exception:
        lexer = TextLexer()
    # nowrap=True allows us to inject the spans into our own <pre> containers
    formatter = HtmlFormatter(nowrap=True)
    return highlight(code, lexer, formatter)

@app.get("/code", tags=["Retrieval"], summary="Get code snippet by SWHID", response_model=CodeSnippetResponse, responses={
    200: {
        "description": "Snippet Retrieved",
        "links": {
            "FindSimilarCode": {
                "operationId": "search_code",
                "requestBody": {
                    "query": "$response.body#/code"
                },
                "description": "Use this code snippet as a query to find similar code across the MediaWiki ecosystem."
            }
        }
    },
    422: {
        "model": CodeValidationErrorResponse,
        "links": {
            "Troubleshoot": {
                "operationId": "health_check",
                "description": "If validation fails unexpectedly, check the system status to ensure the index and database are healthy."
            }
        }
    }
}, operation_id="get_code_snippet")
async def get_code_snippet(swhid: str = Query(..., description="The Software Heritage ID (SWHID) of the content, including line range.", examples=["swh:1:cnt:00003a1a9720cf32009cbe0c3b47256ef1a020bd;origin=https:/github.com/Open-CSP/FlexForm;lines=82-97/"])):
    """
    Retrieves a specific code snippet from the local metadata database.
    The snippet is syntax-highlighted based on the file extension.
    """
    # 1. Extract content hash
    hash_match = re.search(r"swh:1:cnt:([0-9a-f]+)", swhid)
    if not hash_match:
        raise HTTPException(status_code=400, detail="Invalid SWHID format")
    swhid_hash = hash_match.group(1)

    # 2. Look up code and filepath in metadata (SQLite)
    code = None
    filepath = ""
    try:
        with sqlite3.connect(METADATA_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # We match the prefix of swhid or the hash itself
            cursor.execute("SELECT code, filepath FROM functions WHERE swhid LIKE ?", (f"%{swhid_hash}%",))
            row = cursor.fetchone()
            if row:
                code = row["code"]
                filepath = row["filepath"]
    except Exception as e:
        print(f"Database error in get_code_snippet: {e}")
        raise HTTPException(status_code=500, detail="Internal database error")
            
    if not code:
        raise HTTPException(status_code=404, detail="Snippet not found in local database")

    # 3. Highlight
    highlighted = get_highlighted_code(code, filepath)
    return {"code": code, "highlighted_code": highlighted}

@app.post("/search", tags=["Search"], summary="Perform semantic search", response_model=SearchResponse, responses={
    200: {
        "description": "Successful Search",
        "links": {
            "GetCodeSnippet": {
                "operationId": "get_code_snippet",
                "parameters": {
                    "swhid": "$response.body#/results/0/swhid"
                },
                "description": "The `swhid` from any result can be used to retrieve the full snippet via the `/code` endpoint."
            }
        }
    },
    422: {
        "model": ValidationErrorResponse,
        "links": {
            "Troubleshoot": {
                "operationId": "health_check",
                "description": "If your search request is rejected, verify the system status and index health via this link."
            }
        }
    }
}, operation_id="search_code")
async def search_code(req: SearchRequest):
    """
    Performs a semantic search using Jina Code Embeddings.
    The search is performed in two phases:
    1. **Recall**: Find candidate snippets using FAISS vector search.
    2. **Filtering**: Apply metadata filters (repo group, type, language).
    """
    if bi_model is None or index is None:
        raise HTTPException(status_code=503, detail="Server not fully initialised")


    # 1. RECALL PHASE (Bi-Encoder)
    instruction = "Find the most relevant code snippet given the following query:\n"
    xq = bi_model.encode([instruction + req.query], normalize_embeddings=True)
    query_vec = np.array(xq).astype('float32')

    # Retrieve top candidates (performance optimization for CPU)
    RECALL_K = 100
    distances, indices = index.search(query_vec, RECALL_K)
    top_indices = indices[0]

    # Get metadata from SQLite for the top indices
    candidates = []
    valid_indices = [int(idx) for idx in top_indices if idx != -1]
    
    if valid_indices:
        try:
            with sqlite3.connect(METADATA_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Retrieve all relevant metadata in one batch (including the code snippet)
                placeholders = ",".join(["?"] * len(valid_indices))
                query = f"SELECT * FROM functions WHERE id IN ({placeholders})"
                cursor.execute(query, valid_indices)
                rows = cursor.fetchall()
                
                # Map rows by original ID (positional id) to preserve distance info
                meta_map = {row["id"]: dict(row) for row in rows}
                
                for i, idx in enumerate(top_indices):
                    if idx != -1 and int(idx) in meta_map:
                        item = meta_map[int(idx)].copy()
                        # Convert L2 distance to a similarity score (Higher is better)
                        # Formula: 1 / (1 + distance)
                        distance = float(distances[0][i])
                        item["recall_score"] = 1.0 / (1.0 + distance)
                        
                        # Application of filters
                        # Group Filter (Multi-select)
                        group_match = ("all" in req.repo_group or item.get("repo_group") in req.repo_group)
                        
                        # Type Filter (Single-select)
                        type_match = (req.type_filter == "all" or item.get("type") == req.type_filter)
                        
                        # Language Filter (Multi-select, based on file extension)
                        lang_match = "all" in req.language_filter
                        if not lang_match:
                            all_allowed_exts = []
                            for l in req.language_filter:
                                all_allowed_exts.extend(LANGUAGE_EXTENSIONS.get(l, []))
                            
                            filepath = item.get("filepath", "")
                            lang_match = any(filepath.endswith(ext) for ext in all_allowed_exts)
                        
                        if group_match and type_match and lang_match:
                            # Also produce highlighted snippet if code is present in the DB record
                            if item.get("code"):
                                item["highlighted_code"] = get_highlighted_code(item["code"], item.get("filepath", "code.txt"))
                            candidates.append(item)
        except Exception as e:
            print(f"Database error in search_code: {e}")
            raise HTTPException(status_code=500, detail="Internal database error")
    
    if not candidates:
        return {"results": [], "total": 0}

    # Results from Recall + Metadata are already sorted by FAISS L2 distance
    return {"results": candidates[:req.top_k]}


@app.get("/health", tags=["System"], summary="Health check", response_model=HealthResponse, responses={
    200: {
        "description": "System Healthy",
        "links": {
            "PerformSearch": {
                "operationId": "search_code",
                "description": "The system is healthy and index is loaded. You can now perform a semantic search."
            }
        }
    }
}, operation_id="health_check")
def health():
    """
    Returns the current status of the service and the size of the loaded FAISS index.
    """
    return {"status": "ok", "index_size": index.ntotal if index else 0}

# Mount the static frontend directory last to avoid intercepting API calls
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend"))
assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))

if os.path.exists(assets_path):
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
