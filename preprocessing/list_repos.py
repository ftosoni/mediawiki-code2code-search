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

import requests
import json
import sys

HOUND_BASE_URL = "https://codesearch-backend.wmcloud.org"
USER_AGENT = 'mediawiki-repo-fetcher <https://github.com/example/repo>'

# Hound Backends Configuration
BACKENDS = {
    'search': 'Everything',
    'core': 'MediaWiki core',
    'extensions': 'Extensions',
    'skins': 'Skins',
    'things': 'MW extensions & skins',
    'bundled': 'MW tarball',
    'libraries': 'MW libraries',
    'deployed': 'MediaWiki & services at WMF',
    'operations': 'Wikimedia SRE',
    'puppet': 'Puppet',
    'ooui': 'OOUI',
    'milkshake': 'Milkshake',
    'pywikibot': 'Pywikibot',
    'services': 'Wikimedia Services',
    'devtools': 'CI & Development',
    'analytics': 'Data Engineering',
    'wmcs': 'Wikimedia Cloud Services',
    'armchairgm': 'ArmchairGM',
    'shouthow': 'ShoutHow',
    'apps': 'Mobile Apps',
}

# Backends to skip in discovery (usually redundant or internal)
BACKENDS_HIDDEN = [
    'armchairgm', 'extensions', 'milkshake', 'ooui', 'services', 'shouthow', 'skins'
]

def fetch_mediawiki_repos(backend='core'):
    """
    Fetches repository metadata from the Hound API.
    """
    url = f"{HOUND_BASE_URL}/{backend}/api/v1/repos"
    headers = {'User-Agent': USER_AGENT}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract metadata
        repos_subset = []
        for repo_info in data.values():
            if 'url' in repo_info:
                url = repo_info['url']
                # Substitute gerrit-replica with gerrit to bypass the replica
                if url.startswith("https://gerrit-replica."):
                    url = url.replace("https://gerrit-replica.", "https://gerrit.", 1)
                
                repos_subset.append({
                    "url": url,
                    "group": backend
                })
        return repos_subset
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repositories for {backend}: {e}")
        return []

if __name__ == "__main__":
    all_repos = []
    
    # We query all backends EXCEPT the hidden ones to avoid massive redundancy 
    # (e.g. 'things' already includes 'extensions' and 'skins')
    discovery_backends = [b for b in BACKENDS.keys() if b not in BACKENDS_HIDDEN]
    # We also keep 'search' (Everything) as the fallback if explicitly needed, 
    # but the grouped ones are better for filtering.
    
    print("Discovering MediaWiki ecosystem repositories...")
    for be in discovery_backends:
        print(f"  Fetching group: {be} ({BACKENDS[be]})...")
        repos = fetch_mediawiki_repos(be)
        all_repos.extend(repos)
    
    if all_repos:
        # Deduplicate identical URLs (across different backends)
        unique_repos = {r['url']: r for r in all_repos}
        all_repos = list(unique_repos.values())
        
        with open("repos_list.json", "w") as f:
            json.dump(all_repos, f, indent=4)
        print(f"Successfully saved {len(all_repos)} unique repositories to repos_list.json")
    else:
        print("No repositories found.")