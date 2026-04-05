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

import json
import requests
import re
import os
import time

METADATA_PATH = "backend/functions.json"
SWH_SHA1_CACHE = {}

def get_sha1_from_swh(sha1_git):
    """Fetch standard SHA1 from SWH API given a sha1_git."""
    if not sha1_git:
        return None
    if sha1_git in SWH_SHA1_CACHE:
        return SWH_SHA1_CACHE[sha1_git]
    
    url = f"https://archive.softwareheritage.org/api/1/content/sha1_git:{sha1_git}/"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            sha1 = data.get("checksums", {}).get("sha1")
            if sha1:
                SWH_SHA1_CACHE[sha1_git] = sha1
                return sha1
        print(f"  Warning: Could not resolve sha1 for {sha1_git} (Status: {response.status_code})")
    except Exception as e:
        print(f"  Error querying SWH API for {sha1_git}: {e}")
    
    return None

def migrate():
    if not os.path.exists(METADATA_PATH):
        print(f"Error: {METADATA_PATH} not found.")
        return

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"Migrating {len(metadata)} entries...")
    
    updated_count = 0
    for i, item in enumerate(metadata):
        # 1. Remove 'name'
        if "name" in item:
            del item["name"]
        
        # 2. Extract sha1_git from swhid
        swhid = item.get("swhid", "")
        hash_match = re.search(r"swh:1:cnt:([0-9a-f]+)", swhid)
        if hash_match:
            sha1_git = hash_match.group(1)
            # 3. Lookup sha1 if not already present
            if "sha1" not in item:
                sha1 = get_sha1_from_swh(sha1_git)
                if sha1:
                    item["sha1"] = sha1
                    updated_count += 1
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i+1}/{len(metadata)} entries...")
            # Small delay to be polite to the API
            time.sleep(1)

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Migration complete. Updated {updated_count} entries with SHA1.")

if __name__ == "__main__":
    migrate()
