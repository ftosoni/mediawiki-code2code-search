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
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load local environment variables (HF_TOKEN)
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_METADATA_PATH = os.path.join(BASE_DIR, "raw_functions.json")
EMBEDDINGS_NPY_PATH = os.path.join(BASE_DIR, "embeddings.npy")

def generate_embeddings():
    """
    Phase 4a: Load raw metadata, compute embeddings (GPU preferred),
    and save them as a raw NumPy array to embeddings.npy.
    """
    print("\n== MediaWiki Code Search: Neural Vectorization & Embedding Generation (GPU) ==")
    
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
    bi_local_path = os.path.join(MODELS_DIR, "qwen-embeddings")
    
    if os.path.exists(bi_local_path):
        print(f"Loading local model from {bi_local_path}")
        model_path = bi_local_path
    else:
        print(f"Local model not found at {bi_local_path}. Using Hugging Face Hub.")
        model_path = "Qwen/Qwen3-Embedding-0.6B"

    model = SentenceTransformer(
        model_path, 
        trust_remote_code=True, 
        device=device,
        use_auth_token=HF_TOKEN
    )
    model.max_seq_length = 512

    # 2. GENERATE EMBEDDINGS
    print(f"Encoding {len(functions)} snippets with Qwen...")
    code_snippets = [f["code_for_embedding"] for f in functions]
    
    embeddings = model.encode(
        code_snippets, 
        batch_size=16 if device == "cuda" else 2, 
        show_progress_bar=True, 
        normalize_embeddings=True
    )
    
    # 3. SAVE EMBEDDINGS AS NUMPY ARRAY
    print(f"Saving raw embeddings to {EMBEDDINGS_NPY_PATH}...")
    np.save(EMBEDDINGS_NPY_PATH, embeddings)
    print("✅ Embeddings generation complete.")

if __name__ == "__main__":
    generate_embeddings()
