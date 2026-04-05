import os
import json
import hashlib
from pathlib import Path
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
REPOS_LIST_PATH = os.path.join(PREPROC_DIR, "repos_list.json")
LOCAL_REPOS_ROOT = os.path.join(PREPROC_DIR, "mediawiki_repos")
# Intermediate output (unresolved)
UNRESOLVED_METADATA_PATH = os.path.join(PREPROC_DIR, "raw_metadata_unresolved.json")

# Use swh.model if possible for higher precision hashes
try:
    from swh.model.ident import compute_identifier, ObjectType
    SWH_MODEL_AVAILABLE = True
except ImportError:
    SWH_MODEL_AVAILABLE = False

def get_swhid_content_hash(content: bytes) -> str:
    """Calculate the Git-compatible SHA1 (used by SWH) locally."""
    if SWH_MODEL_AVAILABLE:
        res = compute_identifier(ObjectType.CONTENT, {"data": content})
        return str(res)
    else:
        # Standard Git blob hash calculation: "blob <length>\0<content>"
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
                        relative_path = str(filepath.relative_to(repo_path)).replace("\\", "/")
                        
                        for ent in extracted:
                            if not ent["code"].strip(): continue
                            func_hash = hashlib.md5(ent["code"].encode()).hexdigest()
                            
                            repo_entities.append({
                                "id": func_hash,
                                "swhid_hash": swhid_hash,
                                "swh_origin": swh_origin,
                                "repo_name": repo_name,
                                "repo_group": group,
                                "filepath": relative_path,
                                "name": ent["name"],
                                "type": ent["type"],
                                "start_line": ent["start_line"],
                                "end_line": ent["end_line"],
                                "code_for_embedding": ent["code"]
                            })
                except Exception: pass
    return repo_entities

def run_extraction():
    print("== Phase 3a: Fast Structural Entity Extraction (Local Only) ==")
    
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
    print(f"Starting extraction for {total_repos} repositories...")

    all_extracted_entities = []
    start_time = time.time()
    
    # Large parallelization for CPU-bound tasks (Tree-sitter releases GIL)
    max_workers = os.cpu_count() if os.cpu_count() else 4
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
                eta_str = f"{int(eta_s // 60)}m {int(eta_s % 60)}s" if eta_s < 3600 else f"{int(eta_s // 3600)}h {int((eta_s % 3600) // 60)}m"
                print(f"Progress: {completed}/{total_repos} repositories ({(completed/total_repos)*100:.1f}%) - Last: {repo['name']} - ETA: {eta_str}")

    print(f"\nExtraction complete. Total raw entities: {len(all_extracted_entities)}")
    
    with open(UNRESOLVED_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(all_extracted_entities, f, indent=2)
    print(f"Unresolved metadata saved to {UNRESOLVED_METADATA_PATH}")
    print("Next step: Run resolve_swh_hashes.py to map identities.")

if __name__ == "__main__":
    run_extraction()
