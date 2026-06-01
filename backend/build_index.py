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
import faiss
import numpy as np

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "mediawiki.index")
EMBEDDINGS_NPY_PATH = os.path.join(BASE_DIR, "embeddings.npy")

EMBEDDING_DIM = 1024 # Qwen 0.6B dim

def build_index():
    """
    Phase 4b: Load computed raw embeddings from embeddings.npy,
    train and build the FAISS index, and save it to mediawiki.index.
    """
    print("\n== MediaWiki Code Search: FAISS Index Building ==")
    
    if not os.path.exists(EMBEDDINGS_NPY_PATH):
        print(f"Error: {EMBEDDINGS_NPY_PATH} not found. Please run backend/generate_embeddings.py first.")
        return

    print(f"Loading raw embeddings from {EMBEDDINGS_NPY_PATH}...")
    embeddings = np.load(EMBEDDINGS_NPY_PATH)
    num_vectors = embeddings.shape[0]
    print(f"Loaded {num_vectors} vectors with dimension {embeddings.shape[1]}")

    if num_vectors == 0:
        print("No vectors found. Aborting.")
        return

    # 1. BUILD FAISS INDEX
    print("Building FAISS IndexIVFPQ...")
    # nlist: Number of clusters (centroids) for quantization
    # A rule of thumb is 4 * sqrt(N), but for 2,484+ repos we can use a higher fixed value
    nlist = min(100, num_vectors) 
    quantizer = faiss.IndexFlatL2(EMBEDDING_DIM)
    # 32: Number of sub-quantizers, 8: Number of bits per sub-vector
    index = faiss.IndexIVFPQ(quantizer, EMBEDDING_DIM, nlist, 32, 8)
    
    print("Training quantizer...")
    index.train(embeddings.astype('float32'))
    print("Adding vectors to index...")
    index.add(embeddings.astype('float32'))
    
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"Index saved to {FAISS_INDEX_PATH}")
    print("✅ Index building complete.")

if __name__ == "__main__":
    build_index()
