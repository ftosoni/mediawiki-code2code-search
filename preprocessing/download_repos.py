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
import os
import subprocess
import time
import shutil
import stat

def format_eta(seconds):
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"

def rmtree_robust(path):
    """
    shutil.rmtree frequently fails on Windows because:
    1. Git marks object files as read-only.
    2. Other processes (AV, Indexer) might briefly lock a file.
    """
    def remove_readonly(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    for i in range(5): # Up to 5 retries
        try:
            if os.path.exists(path):
                shutil.rmtree(path, onerror=remove_readonly)
            return
        except Exception:
            if i < 4: 
                time.sleep(0.5) # Wait half a second and try again
            else:
                # Final attempt, let it raise or log
                print(f"  ⚠️ Could not remove {path} after 5 attempts.")

# Repositories that are known to hang, require private auth, or are too large for shallow cloning on Windows
BLACKLIST = [
    "LogoutActions", 
    "explicitimages",
    "FinnFrameNet", # Reported timeouts
    "Kotus",
    "Lud",
    "Nimiarkisto",
    "Sanat"
]

def download_repositories(json_file, target_dir="mediawiki_repos"):
    # Enable long paths for Git on Windows to avoid "Filename too long" errors
    try:
        subprocess.run(["git", "config", "--global", "core.longpaths", "true"], check=True)
    except:
        pass

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    with open(json_file, "r") as f:
        repo_data = json.load(f)

    total_repos = len(repo_data)
    print(f"Starting download of {total_repos} repositories...")

    failed_clones = []
    success_count = 0
    skip_count = 0
    start_time = time.time()

    for i, entry in enumerate(repo_data):
        url = entry["url"]
        group = entry["group"]
        
        # Get the repo name from the URL for the folder name
        repo_name = url.split('/')[-1].replace('.git', '')
        group_dir = os.path.join(target_dir, group)
        dest_path = os.path.join(group_dir, repo_name)
        
        # Progress and ETA calc
        processed = i + 1
        elapsed = time.time() - start_time
        avg_time = elapsed / processed if processed > 0 else 0
        eta_seconds = avg_time * (total_repos - processed)
        progress_str = f"[{processed}/{total_repos}]"
        eta_str = f"ETA: {format_eta(eta_seconds)}" if processed > 5 else "ETA: calc..."

        if not os.path.exists(group_dir):
            os.makedirs(group_dir)

        if os.path.exists(dest_path):
            # Basic check: if it's an empty dir, it might be a failed previous attempt
            if not os.listdir(dest_path):
                print(f"{progress_str} Cleaning up empty directory from failed clone: {dest_path}")
                rmtree_robust(dest_path)
            else:
                skip_count += 1
                continue

        # Skip blacklist
        if any(b in url for b in BLACKLIST):
            print(f"{progress_str} Skipping blacklisted/problematic repo {group}/{repo_name}")
            skip_count += 1
            continue

        print(f"{progress_str} Cloning {group}/{repo_name}... ({eta_str})")
        try:
            # Using --depth 1 for a faster, shallow clone
            # Reduced timeout to 60s to avoid hanging on slow/dead connections
            # env={"GIT_TERMINAL_PROMPT": "0"} prevents UI popups for authentication
            # -c credential.helper= ensures system credential managers (like GCM) are bypassed
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"
            
            subprocess.run(["git", "-c", "credential.helper=", "clone", "--depth", "1", url, dest_path], 
                           check=True, capture_output=True, timeout=60, env=env)
            success_count += 1
        except subprocess.TimeoutExpired:
            print(f"  ⚠️ Timeout reached for {url}. Skipping.")
            failed_clones.append({"url": url, "group": group, "reason": "timeout"})
            rmtree_robust(dest_path)
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to clone {url}: {e.stderr.decode().strip()}")
            failed_clones.append({"url": url, "group": group, "reason": "git_error"})
            rmtree_robust(dest_path)
        except Exception as e:
            print(f"  ❌ Unexpected error for {url}: {e}")
            failed_clones.append({"url": url, "group": group, "reason": str(e)})
            rmtree_robust(dest_path)

    # Summary
    print("\n" + "="*40)
    print("Download Phase Complete")
    print(f"Total: {total_repos}")
    print(f"Success: {success_count}")
    print(f"Skipped: {skip_count}")
    print(f"Failed: {len(failed_clones)}")
    print("="*40)

    if failed_clones:
        with open("failed_clones.json", "w") as f:
            json.dump(failed_clones, f, indent=4)
        print(f"List of failed clones saved to failed_clones.json")

if __name__ == "__main__":
    download_repositories("repos_list.json")
