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
from pathlib import Path
import requests
import tree_sitter
import tree_sitter_python
import tree_sitter_cpp
import tree_sitter_c
import tree_sitter_php
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_lua
import tree_sitter_go
import tree_sitter_java
import tree_sitter_rust
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize Languages
PY_LANGUAGE = tree_sitter.Language(tree_sitter_python.language())
CPP_LANGUAGE = tree_sitter.Language(tree_sitter_cpp.language())
C_LANGUAGE = tree_sitter.Language(tree_sitter_c.language())
PHP_LANGUAGE = tree_sitter.Language(tree_sitter_php.language_php())
JS_LANGUAGE = tree_sitter.Language(tree_sitter_javascript.language())
TS_LANGUAGE = tree_sitter.Language(tree_sitter_typescript.language_typescript())
LUA_LANGUAGE = tree_sitter.Language(tree_sitter_lua.language())
GO_LANGUAGE = tree_sitter.Language(tree_sitter_go.language())
JAVA_LANGUAGE = tree_sitter.Language(tree_sitter_java.language())
RUST_LANGUAGE = tree_sitter.Language(tree_sitter_rust.language())

# Paths relative to this script
PREPROC_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PREPROC_DIR, "config.json")
REPOS_LIST_PATH = os.path.join(PREPROC_DIR, "repos_list.json")
LOCAL_REPOS_ROOT = os.path.join(PREPROC_DIR, "mediawiki_repos")
# Output to backend directory for keep it ready for vectorization
RAW_METADATA_PATH = os.path.join(PREPROC_DIR, "..", "backend", "raw_functions.json")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"user_agent": "mediawiki-repo-fetcher", "swh_token": ""}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

# Global Config
GLOBAL_CONFIG = load_config()

# Use swh.model if possible for higher precision hashes
try:
    from swh.model.ident import compute_identifier, ObjectType
    SWH_MODEL_AVAILABLE = True
except ImportError:
    SWH_MODEL_AVAILABLE = False

# Cache for SHA1 Git -> Standard SHA1 resolver (SWH API)
SWH_SHA1_CACHE_PATH = os.path.join(PREPROC_DIR, "swh_sha1_cache.json")
SWH_SHA1_CACHE = {}
SWH_CACHE_LOCK = threading.Lock()
SWH_API_LOCK = threading.Lock() # Maintain single-threaded network access

def load_swh_cache():
    global SWH_SHA1_CACHE
    if os.path.exists(SWH_SHA1_CACHE_PATH):
        try:
            with open(SWH_SHA1_CACHE_PATH, "r") as f:
                SWH_SHA1_CACHE = json.load(f)
            print(f"Loaded {len(SWH_SHA1_CACHE)} entries from SWH SHA1 cache.")
        except Exception as e:
            print(f"Warning: Failed to load SWH cache: {e}")

def save_swh_cache():
    with SWH_CACHE_LOCK:
        try:
            with open(SWH_SHA1_CACHE_PATH, "w") as f:
                json.dump(SWH_SHA1_CACHE, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save SWH cache: {e}")

load_swh_cache()

def get_sha1_from_swh(sha1_git: str) -> str:
    # 1. Fast path: check cache without blocking API access
    with SWH_CACHE_LOCK:
        if sha1_git in SWH_SHA1_CACHE:
            return SWH_SHA1_CACHE[sha1_git]
    
    # 2. Slow path: Acquire API lock for network access
    with SWH_API_LOCK:
        # Double-check if someone else filled the cache while we waited for the lock
        with SWH_CACHE_LOCK:
            if sha1_git in SWH_SHA1_CACHE:
                return SWH_SHA1_CACHE[sha1_git]
        
        url = f"https://archive.softwareheritage.org/api/1/content/sha1_git:{sha1_git}/"
        headers = {
            "User-Agent": GLOBAL_CONFIG.get("user_agent", "mediawiki-repo-fetcher"),
            "Accept": "application/json"
        }
        if GLOBAL_CONFIG.get("swh_token"):
            headers["Authorization"] = f"Bearer {GLOBAL_CONFIG['swh_token']}"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                sha1 = data.get("checksums", {}).get("sha1")
                if sha1:
                    with SWH_CACHE_LOCK:
                        SWH_SHA1_CACHE[sha1_git] = sha1
                    return sha1
            elif response.status_code == 429:
                pass
        except Exception:
            pass
        return None

def get_swhid_content_hash(content: bytes) -> str:
    if SWH_MODEL_AVAILABLE:
        res = compute_identifier(ObjectType.CONTENT, {"data": content})
        return str(res)
    else:
        header = f"blob {len(content)}\0".encode()
        return hashlib.sha1(header + content).hexdigest()

def extract_entity_name(node, code_bytes: bytes) -> str:
    if node.type == "template_declaration":
        for child in reversed(node.children):
            if child.type not in ["template", "template_parameter_list", "<", ">", ",", "comment", ";"]:
                name = extract_entity_name(child, code_bytes)
                if name and name != "unknown":
                    return name
    name_node = node.child_by_field_name("name")
    if not name_node:
        def find_name(n):
            if n.type in ["identifier", "field_identifier", "type_identifier", "name"]:
                return n
            for child in n.children:
                found = find_name(child)
                if found: return found
            return None
        name_node = find_name(node)
    
    if name_node:
        return code_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8', errors='ignore')
    return "unknown"

def extract_code_entities(code_bytes: bytes, ext: str) -> list:
    if ext == ".py":
        lang = PY_LANGUAGE
        query_scm = "(function_definition) @function (class_definition) @type"
    elif ext in [".cpp", ".hpp", ".h", ".cc", ".cxx"]:
        lang = CPP_LANGUAGE
        query_scm = """
            (template_declaration (function_definition)) @template_function
            (template_declaration [(class_specifier) (struct_specifier) (enum_specifier) (alias_declaration)]) @template_type
            (function_definition) @function
            (class_specifier) @type
            (struct_specifier) @type
            (enum_specifier) @type
            (alias_declaration) @type
        """
    elif ext == ".c":
        lang = C_LANGUAGE
        query_scm = "(function_definition) @function (struct_specifier) @type (union_specifier) @type (enum_specifier) @type"
    elif ext == ".php" or ext == ".inc":
        lang = PHP_LANGUAGE
        query_scm = "(function_definition) @function (method_declaration) @function (class_declaration) @type (interface_declaration) @type (trait_declaration) @type (enum_declaration) @type"
    elif ext == ".js":
        lang = JS_LANGUAGE
        query_scm = "(function_declaration) @function (method_definition) @function (class_declaration) @type"
    elif ext in [".ts", ".tsx", ".mts", ".cts"]:
        lang = TS_LANGUAGE
        query_scm = "(function_declaration) @function (method_definition) @function (class_declaration) @type (interface_declaration) @type (enum_declaration) @type (type_alias_declaration) @type"
    elif ext == ".lua":
        lang = LUA_LANGUAGE
        query_scm = "(function_declaration) @function"
    elif ext == ".go":
        lang = GO_LANGUAGE
        query_scm = "(function_declaration) @function (method_declaration) @function (type_declaration) @type"
    elif ext == ".java":
        lang = JAVA_LANGUAGE
        query_scm = "(method_declaration) @function (class_declaration) @type (interface_declaration) @type (enum_declaration) @type (record_declaration) @type"
    elif ext == ".rs":
        lang = RUST_LANGUAGE
        query_scm = "(function_item) @function (struct_item) @type (enum_item) @type (trait_item) @type (type_item) @type"
    else:
        return []

    try:
        parser = tree_sitter.Parser(lang)
        tree = parser.parse(code_bytes)
        query = tree_sitter.Query(lang, query_scm)
        cursor = tree_sitter.QueryCursor(query)
        captures_dict = cursor.captures(tree.root_node)
    except Exception:
        return []

    all_captures = []
    for entity_type, nodes in captures_dict.items():
        for node in nodes:
            all_captures.append((node, entity_type))

    all_captures.sort(key=lambda x: (x[0].end_byte - x[0].start_byte), reverse=True)

    final_nodes = []
    # Mapping for deduplication grouping.
    category_map = {
        "template_function": "template_function", 
        "template_type": "template_type", 
        "function": "function", 
        "type": "type"
    }
    covered_ranges = {"function": [], "type": [], "template_function": [], "template_type": []}
    
    for node, entity_type in all_captures:
        node_start, node_end = node.start_byte, node.end_byte
        name = extract_entity_name(node, code_bytes)
        logical_cat = category_map.get(entity_type, entity_type)
        
        is_covered = False
        if logical_cat in covered_ranges:
            for (c_start, c_end, c_name) in covered_ranges[logical_cat]:
                if node_start >= c_start and node_end <= c_end:
                    if name == c_name or name == "unknown":
                        is_covered = True
                        break
        
        if not is_covered:
            final_nodes.append((node, entity_type))
            if logical_cat not in covered_ranges: covered_ranges[logical_cat] = []
            covered_ranges[logical_cat].append((node_start, node_end, name))

    entities = []
    for node, entity_type in final_nodes:
        name = extract_entity_name(node, code_bytes)
        current_start = node.start_byte
        actual_start_line = node.start_point[0] + 1
        prev = node.prev_sibling
        while prev and prev.type in ["comment", "line_comment", "block_comment"]:
            current_start = prev.start_byte
            actual_start_line = prev.start_point[0] + 1
            prev = prev.prev_sibling
        
        code = code_bytes[current_start:node.end_byte].decode('utf-8', errors='ignore')
        entities.append({
            "name": name,
            "start_line": actual_start_line,
            "end_line": node.end_point[0] + 1,
            "code": code,
            "type": entity_type
        })
    return entities

def process_repository(repo_info, group_dir, valid_exts):
    repo_name = repo_info["name"]
    group = repo_info["group"]
    repo_path = os.path.join(group_dir, repo_name)
    swh_origin = repo_info["url"].replace("https://", "https:/")
    
    repo_entities = []
    
    if not os.path.isdir(repo_path):
        return []

    for root, _, files in os.walk(repo_path):
        if ".git" in root: continue
        for file in files:
            ext = Path(file).suffix
            if ext in valid_exts:
                filepath = Path(root) / file
                try:
                    with open(filepath, "rb") as f:
                        code_bytes = f.read()
                    
                    text_lf = code_bytes.replace(b"\r\n", b"\n")
                    extracted = extract_code_entities(text_lf, ext)
                    
                    if extracted:
                        swhid_hash = get_swhid_content_hash(text_lf)
                        # Call SWH API only once per file if entities extracted
                        sha1 = get_sha1_from_swh(swhid_hash)
                        
                        relative_path = str(filepath.relative_to(repo_path)).replace("\\", "/")
                        
                        for ent in extracted:
                            if not ent["code"].strip(): continue
                            func_hash = hashlib.md5(ent["code"].encode()).hexdigest()
                            swhid = f"swh:1:cnt:{swhid_hash};origin={swh_origin};lines={ent['start_line']}-{ent['end_line']}/"
                            
                            repo_entities.append({
                                "id": func_hash,
                                "swhid": swhid,
                                "sha1": sha1,
                                "repo_name": repo_name,
                                "repo_group": group,
                                "filepath": relative_path,
                                "name": ent["name"],
                                "type": ent["type"],
                                "code_for_embedding": ent["code"]
                            })
                except Exception: pass
    return repo_entities

def run_extraction():
    print("== MediaWiki Code Search: Massive Parallel Entity Extraction Phase ==")
    
    if not os.path.exists(REPOS_LIST_PATH):
        print(f"Error: {REPOS_LIST_PATH} not found.")
        return
    with open(REPOS_LIST_PATH, "r") as f:
        repo_metadata_list = json.load(f)
    
    repo_lookup_base = {e["url"].split('/')[-1].replace('.git', ''): e for e in repo_metadata_list}

    if not os.path.exists(LOCAL_REPOS_ROOT):
        print(f"Error: {LOCAL_REPOS_ROOT} not found.")
        return

    valid_exts = {".c", ".cpp", ".h", ".hpp", ".cc", ".cxx", ".py", ".php", ".inc", ".js", ".ts", ".tsx", ".mts", ".cts", ".lua", ".go", ".java", ".rs"}

    # Discovery
    discovery_list = []
    groups = [d for d in os.listdir(LOCAL_REPOS_ROOT) if os.path.isdir(os.path.join(LOCAL_REPOS_ROOT, d))]
    for group in groups:
        group_dir = os.path.join(LOCAL_REPOS_ROOT, group)
        repos = [d for d in os.listdir(group_dir) if os.path.isdir(os.path.join(group_dir, d))]
        for repo_name in repos:
            repo_info = repo_lookup_base.get(repo_name, {"url": f"https://unknown/{repo_name}", "group": group})
            discovery_list.append({
                "name": repo_name,
                "group": group,
                "group_dir": group_dir,
                "url": repo_info["url"]
            })

    total_repos = len(discovery_list)
    print(f"Discovered {total_repos} repositories. Starting parallel extraction...")

    all_extracted_entities = []
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor to handle mix of IO and CPU
    max_workers = os.cpu_count() * 2 if os.cpu_count() else 8
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_repo = {
            executor.submit(process_repository, repo, repo["group_dir"], valid_exts): repo 
            for repo in discovery_list
        }
        
        completed = 0
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                entities = future.result()
                all_extracted_entities.extend(entities)
            except Exception as exc:
                print(f"Repo {repo['name']} generated an exception: {exc}")
            
            completed += 1
            if completed % 10 == 0 or completed == total_repos:
                elapsed = time.time() - start_time
                avg_time = elapsed / completed
                remaining = total_repos - completed
                eta_s = avg_time * remaining
                
                if eta_s > 3600:
                    eta_str = f"{int(eta_s // 3600)}h {int((eta_s % 3600) // 60)}m"
                elif eta_s > 60:
                    eta_str = f"{int(eta_s // 60)}m {int(eta_s % 60)}s"
                else:
                    eta_str = f"{int(eta_s)}s"
                
                print(f"Progress: {completed}/{total_repos} repositories processed ({(completed/total_repos)*100:.1f}%) - Last finished: {repo['name']} - ETA: {eta_str}")
            
            # Periodically save cache to disk
            if completed % 50 == 0:
                save_swh_cache()

    # Deduplicate entities by ID
    unique_entities = {e["id"]: e for e in all_extracted_entities}
    final_list = list(unique_entities.values())
    
    print(f"\nExtraction complete. Total unique entities: {len(final_list)}")
    
    os.makedirs(os.path.dirname(RAW_METADATA_PATH), exist_ok=True)
    with open(RAW_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2)
    save_swh_cache()
    print(f"Intermediate metadata saved to {RAW_METADATA_PATH}")

if __name__ == "__main__":
    run_extraction()

