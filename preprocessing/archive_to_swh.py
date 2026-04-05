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
import os
import sys

# Path handling relative to script location
PREPROC_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PREPROC_DIR, "config.json")
REPOS_FILE = os.path.join(PREPROC_DIR, "repos_list.json")
SWH_API_URL = "https://archive.softwareheritage.org/api/1/origin/save/bulk/"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found. Please create it first.")
        sys.exit(1)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

import time

def archive_repos():
    config = load_config()
    BATCH_SIZE = 400
    LOG_FILE = os.path.join(PREPROC_DIR, "swh_request_log.json")
    
    if not os.path.exists(REPOS_FILE):
        print(f"Error: {REPOS_FILE} not found. Run the listing script first.")
        return

    with open(REPOS_FILE, "r") as f:
        repos = json.load(f)

    headers = {
        "User-Agent": config["user_agent"],
        "Authorization": f"Bearer {config['swh_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print(f"Total repositories to archive: {len(repos)}")
    print(f"Batch mode enabled: {BATCH_SIZE} repos per request.\n")

    request_history = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                request_history = json.load(f)
            except json.JSONDecodeError:
                request_history = []

    for i in range(0, len(repos), BATCH_SIZE):
        batch = repos[i:i + BATCH_SIZE]
        
        # Prepare data in the JSON format required by SWH
        payload = [
            {"origin_url": repo["url"], "visit_type": config.get("visit_type", "git")}
            for repo in batch
        ]

        print(f"[{i//BATCH_SIZE + 1}/{(len(repos)-1)//BATCH_SIZE + 1}] Sending batch of {len(payload)} origins...")

        try:
            response = requests.post(SWH_API_URL, json=payload, headers=headers, timeout=60)
            
            if response.status_code in [200, 201]:
                result = response.json()
                req_id = result.get("request_id")
                print(f"✅ Success! Request ID: {req_id}")
                
                request_history.append({
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "batch_index": i // BATCH_SIZE,
                    "count": len(payload),
                    "request_id": req_id,
                    "status": "success"
                })
            else:
                print(f"❌ Batch failed with status {response.status_code}")
                print(response.text)
                request_history.append({
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "batch_index": i // BATCH_SIZE,
                    "count": len(payload),
                    "error": response.text,
                    "status_code": response.status_code,
                    "status": "failed"
                })
            
            # Save progress to log file
            with open(LOG_FILE, "w") as f:
                json.dump(request_history, f, indent=4)
            
            # Small delay to respect rate limits
            if i + BATCH_SIZE < len(repos):
                # Using a slightly longer delay to be safe
                time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the request: {e}")
            break

    print(f"\nArchiving process completed. History saved to {LOG_FILE}")

if __name__ == "__main__":
    archive_repos()