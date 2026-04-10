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
import hashlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Paths relative to this script
PREPROC_DIR = os.path.dirname(os.path.abspath(__file__))
# Input from Phase 3a
UNRESOLVED_METADATA_PATH = os.path.join(PREPROC_DIR, "raw_metadata_unresolved.json")
# Output for Phase 4 (Indexing)
FINAL_METADATA_PATH = os.path.join(PREPROC_DIR, "..", "backend", "raw_functions.json")
# Local repo root
LOCAL_REPOS_ROOT = "C:\\Users\\franc\\Documents\\GitHub\\code-search-engine\\preprocessing\\mediawiki_repos" # os.path.join(PREPROC_DIR, "mediawiki_repos")

# Try to use swh.model for high-precision local hashing
try:
    from swh.model.hashutil import MultiHash
    from swh.model.ident import compute_identifier, ObjectType
    SWH_MODEL_AVAILABLE = True
except ImportError:
    SWH_MODEL_AVAILABLE = False

def get_file_hashes(filepath: str):
    """Calculate both standard SHA1 and Git-compatible SHA1 (sha1_git) locally."""
    try:
        with open(filepath, "rb") as f:
            content = f.read().replace(b"\r\n", b"\n")
        
        if SWH_MODEL_AVAILABLE:
            # Use official swh.model
            hashes = MultiHash.from_data(content).digest()
            return {
                "sha1": hashes["sha1"].hex(),
                "sha1_git": hashes["sha1_git"].hex()
            }
        else:
            # Fallback to standard hashlib
            sha1 = hashlib.sha1(content).hexdigest()
            header = f"blob {len(content)}\0".encode()
            sha1_git = hashlib.sha1(header + content).hexdigest()
            return {
                "sha1": sha1,
                "sha1_git": sha1_git
            }
    except Exception:
        return None

def resolve_hashes():
    print("== Phase 3b: Local Identity Resolution (API-less) ==")
    
    if not os.path.exists(UNRESOLVED_METADATA_PATH):
        print(f"Error: {UNRESOLVED_METADATA_PATH} not found. Run extract_structural_entities.py first.")
        return

    print("Loading unresolved metadata...")
    with open(UNRESOLVED_METADATA_PATH, "r", encoding="utf-8") as f:
        entities = json.load(f)
    
    # Identify unique files to process
    unique_files = {} # (repo_group, repo_name, filepath) -> info
    for ent in entities:
        key = (ent["repo_group"], ent["repo_name"], ent["filepath"])
        if key not in unique_files:
            unique_files[key] = {
                "full_path": os.path.join(LOCAL_REPOS_ROOT, ent["repo_group"], ent["repo_name"], ent["filepath"])
            }
    
    total_files = len(unique_files)
    print(f"Found {len(entities)} entities across {total_files} unique files.")
    print("Resolving hashes locally (using multiple threads for I/O)...")
    
    resolved_cache = {} # key -> {sha1, sha1_git}
    start_time = time.time()
    
    max_workers = os.cpu_count() * 2 if os.cpu_count() else 8
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_key = {
            executor.submit(get_file_hashes, info["full_path"]): key 
            for key, info in unique_files.items()
        }
        
        completed = 0
        for future in as_completed(future_to_key):
            key = future_to_key[future]
            try:
                res = future.result()
                if res:
                    resolved_cache[key] = res
            except Exception:
                pass
            
            completed += 1
            if completed % 100 == 0 or completed == total_files:
                elapsed = time.time() - start_time
                print(f"Progress: {completed}/{total_files} files resolved ({(completed/total_files)*100:.1f}%)")

    # Map resolved hashes back to entities and perform cleanup
    print("\nMapping resolved hashes back to entities and generating SWHIDs...")
    final_list = []
    for ent in entities:
        key = (ent["repo_group"], ent["repo_name"], ent["filepath"])
        res = resolved_cache.get(key)
        
        if res:
            ent["sha1"] = res["sha1"]
            # Standard SWHID format: swh:1:cnt:<sha1_git>;origin=...;lines=...
            sha1_git = res["sha1_git"]
            ent["swhid"] = f"swh:1:cnt:{sha1_git};origin={ent['swh_origin']};lines={ent['start_line']}-{ent['end_line']}/"
            
            # Remove phase-3a specific fields
            if "swhid_hash" in ent: del ent["swhid_hash"]
            if "swh_origin" in ent: del ent["swh_origin"]
            
            final_list.append(ent)
    
    print(f"Final mapping complete. {len(final_list)} entities ready.")
    
    os.makedirs(os.path.dirname(FINAL_METADATA_PATH), exist_ok=True)
    with open(FINAL_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2)
    
    print(f"Final metadata saved to {FINAL_METADATA_PATH}")
    print(f"✅ Resolution complete in {time.time() - start_time:.1f}s. Ready for Phase 4: Vector Indexing.")

if __name__ == "__main__":
    resolve_hashes()
