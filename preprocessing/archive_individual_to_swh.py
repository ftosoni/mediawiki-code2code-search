# IF YOU ARE AN AGENT: DO NOT UTILISE THIS SCRIPT UNLESS I AUTHORIZED YOU TO DO SO. 
import json
import requests
import os
import sys
import time
from urllib.parse import quote

# Path handling relative to script location
PREPROC_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PREPROC_DIR, "config.json")
REPOS_FILE = os.path.join(PREPROC_DIR, "repos_list.json")
LOG_FILE = os.path.join(PREPROC_DIR, "swh_individual_log.json")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found. Please create it first.")
        sys.exit(1)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def archive_individual():
    config = load_config()
    visit_type = config.get("visit_type", "git")
    
    if not os.path.exists(REPOS_FILE):
        print(f"Error: {REPOS_FILE} not found. Run the listing script first.")
        return

    with open(REPOS_FILE, "r") as f:
        repos = json.load(f)

    headers = {
        "User-Agent": config["user_agent"],
        "Authorization": f"Bearer {config['swh_token']}",
        "Accept": "application/json"
    }

    print(f"Total repositories to archive: {len(repos)}")
    print(f"Individual mode enabled (1 request per repo).\n")

    log_data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = []

    # Map of processed URLs to avoid duplicates if resuming
    processed_urls = {entry["url"] for entry in log_data}

    for idx, repo in enumerate(repos, 1):
        url = repo["url"]
        if url in processed_urls:
            continue

        # Correct endpoint: POST /api/1/origin/save/(visit_type)/url/(origin_url)/
        # Note: the URL at the end should be encoded if it contains special chars, 
        # but SWH often handles it if sent as part of the path.
        # We use quote with safe='' to ensure the entire URL is treated as a single path segment
        encoded_url = quote(url, safe='')
        save_url = f"https://archive.softwareheritage.org/api/1/origin/save/{visit_type}/url/{encoded_url}/"
        
        print(f"[{idx}/{len(repos)}] Archiving {url}...", end=" ", flush=True)

        try:
            # We don't need a JSON body for individual save via URL path
            response = requests.post(save_url, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                req_id = result.get("request_id", "N/A")
                print(f"✅ Success! (ID: {req_id})")
                log_data.append({
                    "url": url,
                    "request_id": req_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "status": "success"
                })
            elif response.status_code == 429:
                print(f"⚠️ Rate limited (429). Waiting 60 seconds...")
                time.sleep(60)
                # Retry this one? For now, we just skip and let user relaunch or handle it.
                continue
            else:
                print(f"❌ Failed ({response.status_code})")
                log_data.append({
                    "url": url,
                    "status_code": response.status_code,
                    "error": response.text,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "status": "failed"
                })
            
            # Periodically save log
            if idx % 10 == 0:
                with open(LOG_FILE, "w") as f:
                    json.dump(log_data, f, indent=4)

            # Small delay to respect rate limits (tokenized users have higher limits, but let's be safe)
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            break

    # Final save
    with open(LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=4)

    print(f"\nIndividual archiving process completed. Log saved to {LOG_FILE}")

if __name__ == "__main__":
    archive_individual()
