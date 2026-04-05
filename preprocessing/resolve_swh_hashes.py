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
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Paths relative to this script
PREPROC_DIR = os.path.dirname(os.path.abspath(__file__))
# Input from Phase 3a
UNRESOLVED_METADATA_PATH = os.path.join(PREPROC_DIR, "raw_metadata_unresolved.json")
# Output for Phase 4 (Indexing)
FINAL_METADATA_PATH = os.path.join(PREPROC_DIR, "..", "backend", "raw_functions.json")
# Cache for persistence
SWH_SHA1_CACHE_PATH = os.path.join(PREPROC_DIR, "swh_sha1_cache.json")

# Config (shared with other scripts)
GLOBAL_CONFIG = {}
CONFIG_PATH = os.path.join(PREPROC_DIR, "config.json")
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        GLOBAL_CONFIG = json.load(f)

# Locking and Cache
SWH_SHA1_CACHE = {}
SWH_CACHE_LOCK = threading.Lock()
SWH_API_LOCK = threading.Lock() # Maintain single-threaded network access for SWH API

def load_swh_cache():
    global SWH_SHA1_CACHE
    if os.path.exists(SWH_SHA1_CACHE_PATH):
        try:
            with open(SWH_SHA1_CACHE_PATH, "r") as f:
                SWH_SHA1_CACHE = json.load(f)
            print(f"Loaded {len(SWH_SHA1_CACHE)} entries from persistent SHA1 cache.")
        except Exception as e:
            print(f"Warning: Failed to load SWH cache: {e}")

def save_swh_cache():
    with SWH_CACHE_LOCK:
        try:
            with open(SWH_SHA1_CACHE_PATH, "w") as f:
                json.dump(SWH_SHA1_CACHE, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save SWH cache: {e}")

def get_sha1_from_swh(swhid_hash: str) -> str:
    """Resolve Git-compatible SHA1 to standard SHA1 via SWH API."""
    # 1. Fast path: check cache
    with SWH_CACHE_LOCK:
        if swhid_hash in SWH_SHA1_CACHE:
            return SWH_SHA1_CACHE[swhid_hash]
    
    # 2. Slow path: Network request (Single-threaded to respect user limit)
    with SWH_API_LOCK:
        # Double check cache
        with SWH_CACHE_LOCK:
            if swhid_hash in SWH_SHA1_CACHE:
                return SWH_SHA1_CACHE[swhid_hash]
        
        url = f"https://archive.softwareheritage.org/api/1/content/sha1_git:{swhid_hash}/"
        headers = {
            "User-Agent": GLOBAL_CONFIG.get("user_agent", "mediawiki-repo-fetcher"),
            "Accept": "application/json"
        }
        if GLOBAL_CONFIG.get("swh_token"):
            headers["Authorization"] = f"Bearer {GLOBAL_CONFIG['swh_token']}"

        try:
            # Short sleep to be polite if needed, but the lock already limits us
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                sha1 = data.get("checksums", {}).get("sha1")
                if sha1:
                    with SWH_CACHE_LOCK:
                        SWH_SHA1_CACHE[swhid_hash] = sha1
                    return sha1
            elif response.status_code == 404:
                # Store null so we don't keep asking for non-existent content
                with SWH_CACHE_LOCK:
                    SWH_SHA1_CACHE[swhid_hash] = None
            elif response.status_code == 429:
                print("⚠️ SWH Rate limit hit. Waiting 60s...")
                time.sleep(60)
        except Exception:
            pass
        return None

def resolve_hashes():
    print("== Phase 3b: SWH Identity Resolution (Network-Bound) ==")
    
    if not os.path.exists(UNRESOLVED_METADATA_PATH):
        print(f"Error: {UNRESOLVED_METADATA_PATH} not found. Run extract_structural_entities.py first.")
        return
        
    load_swh_cache()
    
    with open(UNRESOLVED_METADATA_PATH, "r", encoding="utf-8") as f:
        entities = json.load(f)
    
    # Identify unique hashes to resolve
    unique_hashes = list(set(e["swhid_hash"] for e in entities))
    unresolved_hashes = [h for h in unique_hashes if h not in SWH_SHA1_CACHE]
    
    print(f"Total entities: {len(entities)}")
    print(f"Unique file hashes: {len(unique_hashes)}")
    print(f"Already cached: {len(unique_hashes) - len(unresolved_hashes)}")
    print(f"Need to resolve: {len(unresolved_hashes)}")
    
    if unresolved_hashes:
        print("Starting network resolution (using single-threaded API lock)...")
        start_time = time.time()
        
        # We can use multiple threads to check the cache, but only one will hit the API
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(get_sha1_from_swh, h): h for h in unresolved_hashes}
            
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 10 == 0 or completed == len(unresolved_hashes):
                    elapsed = time.time() - start_time
                    avg = elapsed / completed
                    eta = avg * (len(unresolved_hashes) - completed)
                    print(f"Progress: {completed}/{len(unresolved_hashes)} hashes resolved ({(completed/len(unresolved_hashes))*100:.1f}%) - ETA: {int(eta//60)}m {int(eta%60)}s")
                
                # Periodic save
                if completed % 100 == 0:
                    save_swh_cache()

    # Final mapping
    print("\nMapping resolved hashes back to entities...")
    for ent in entities:
        swhid_hash = ent["swhid_hash"]
        sha1 = SWH_SHA1_CACHE.get(swhid_hash)
        ent["sha1"] = sha1
        # Construct final SWHID with standard format
        # swh:1:cnt:<sha1_git>;origin=...;lines=...
        ent["swhid"] = f"swh:1:cnt:{swhid_hash};origin={ent['swh_origin']};lines={ent['start_line']}-{ent['end_line']}/"
        # Cleanup intermediate fields
        del ent["swhid_hash"]
        del ent["swh_origin"]

    os.makedirs(os.path.dirname(FINAL_METADATA_PATH), exist_ok=True)
    with open(FINAL_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(entities, f, indent=2)
    
    save_swh_cache()
    print(f"Final metadata saved to {FINAL_METADATA_PATH}")
    print("✅ Resolution complete. Ready for Phase 4: Vector Indexing.")

if __name__ == "__main__":
    resolve_hashes()
