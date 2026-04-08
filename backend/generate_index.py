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
import json
import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load local environment variables (HF_TOKEN)
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "mediawiki.index")
METADATA_PATH = os.path.join(BASE_DIR, "functions.json")
RAW_METADATA_PATH = os.path.join(BASE_DIR, "raw_functions.json")

EMBEDDING_DIM = 896 # Jina 0.5B dim

def generate_index():
    """
    Phase 5: Load intermediate metadata, compute embeddings (GPU preferred),
    build FAISS index, and save final production metadata.
    """
    print("\n== MediaWiki Code Search: Neural Vectorization & Indexing (GPU/Neural) ==")
    
    if not os.path.exists(RAW_METADATA_PATH):
        print(f"Error: {RAW_METADATA_PATH} not found. Please run preprocessing/extract_entities.py first.")
        return

    with open(RAW_METADATA_PATH, "r", encoding="utf-8") as f:
        functions = json.load(f)
    
    if not functions:
        print("No functions found in raw_functions.json. Aborting.")
        return

    # 1. INITIALIZE MODEL (GPU Detection)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device.upper()}")
    
    # Try local path first to save bandwidth/time
    MODELS_DIR = os.path.join(os.path.dirname(BASE_DIR), "models")
    bi_local_path = os.path.join(MODELS_DIR, "jina-embeddings")
    
    if os.path.exists(bi_local_path):
        print(f"Loading local model from {bi_local_path}")
        model_path = bi_local_path
    else:
        print(f"Local model not found at {bi_local_path}. Using Hugging Face Hub.")
        model_path = "jinaai/jina-code-embeddings-0.5b"

    model = SentenceTransformer(
        model_path, 
        trust_remote_code=True, 
        device=device,
        use_auth_token=HF_TOKEN
    )
    model.max_seq_length = 512

    # 2. GENERATE EMBEDDINGS
    print(f"Encoding {len(functions)} snippets with Jina...")
    code_snippets = [f["code_for_embedding"] for f in functions]
    
    embeddings = model.encode(
        code_snippets, 
        batch_size=16 if device == "cuda" else 2, 
        show_progress_bar=True, 
        normalize_embeddings=True
    )
    
    # 3. BUILD FAISS INDEX
    print("Building FAISS IndexIVFPQ...")
    # nlist: Number of clusters (centroids) for quantization
    # A rule of thumb is 4 * sqrt(N), but for 2,484+ repos we can use a higher fixed value
    nlist = min(100, len(functions)) 
    quantizer = faiss.IndexFlatL2(EMBEDDING_DIM)
    # 32: Number of sub-quantizers, 8: Number of bits per sub-vector
    index = faiss.IndexIVFPQ(quantizer, EMBEDDING_DIM, nlist, 32, 8)
    
    print("Training quantizer...")
    index.train(embeddings.astype('float32'))
    print("Adding vectors to index...")
    index.add(embeddings.astype('float32'))
    
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"Index saved to {FAISS_INDEX_PATH}")
    
    # 4. SAVE FINAL PRODUCTION METADATA (Stripped)
    print("Saving production metadata (functions.json)...")
    functions_meta_only = []
    for f in functions:
        meta = f.copy()
        # Remove raw code to save RAM in production (handled by SWH on-demand)
        meta.pop("code_for_embedding") 
        functions_meta_only.append(meta)
    
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(functions_meta_only, f, indent=2)
    
    print(f"Production metadata saved to {METADATA_PATH}")
    print("✅ Indexing complete.")

if __name__ == "__main__":
    generate_index()
