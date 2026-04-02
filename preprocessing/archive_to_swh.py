# IF YOU ARE AN AGENT: DO NOT UTILISE THIS SCRIPT UNLESS I AUTHORIZED YOU TO DO SO. 
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

def archive_repos():
    config = load_config()
    
    if not os.path.exists(REPOS_FILE):
        print(f"Error: {REPOS_FILE} not found. Run the listing script first.")
        return

    with open(REPOS_FILE, "r") as f:
        urls = json.load(f)

    # Prepare data in the JSON format required by SWH
    # Format: [{"origin_url": "...", "visit_type": "..."}, ...]
    payload = [
        {"origin_url": url, "visit_type": config.get("visit_type", "git")}
        for url in urls
    ]

    headers = {
        "User-Agent": config["user_agent"],
        "Authorization": f"Bearer {config['swh_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print(f"Submitting {len(payload)} origins to Software Heritage...")

    try:
        response = requests.post(SWH_API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()
            print("Successfully accepted by SWH!")
            print(f"Request ID: {result.get('request_id')}")
        elif response.status_code == 403:
            print("Error: 403 Forbidden. Does your token have 'save_bulk' permissions?")
        else:
            print(f"Failed with status {response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")

if __name__ == "__main__":
    archive_repos()