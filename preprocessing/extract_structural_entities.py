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
    """Recursively find the most appropriate name for a code entity."""
    if node.type == "template_declaration":
        # Look for the entity being templated (last child usually)
        for child in reversed(node.children):
            if child.type not in ["template", "template_parameter_list", "<", ">", ",", "comment", ";"]:
                return extract_entity_name(child, code_bytes)
    
    # Standard field names in Tree-sitter
    name_node = node.child_by_field_name("name")
    if not name_node and node.type in ["function_definition", "declaration"]:
        # For functions, the name is deep inside the declarator
        declarator = node.child_by_field_name("declarator")
        if declarator:
            def find_identifier(n):
                if n.type in ["identifier", "destructor_name", "qualified_identifier", "field_identifier"]:
                    return n
                # If it's a pointer/reference/function declarator, drill down to the inner declarator
                if n.type in ["function_declarator", "pointer_declarator", "reference_declarator", "array_declarator"]:
                    # Usually the 'declarator' field or the first non-punctuation child
                    inner = n.child_by_field_name("declarator")
                    if inner: return find_identifier(inner)
                    for child in n.children:
                        if child.type not in ["(", ")", "*", "&", "[", "]", "comment"]:
                            res = find_identifier(child)
                            if res: return res
                return None
            name_node = find_identifier(declarator)
            
    if not name_node:
        # Fallback recursive search for identifiers
        def find_name(n):
            if n.type in ["identifier", "field_identifier", "type_identifier", "name"]:
                return n
            for child in n.children:
                found = find_name(child)
                if found: return found
            return None
        name_node = find_name(node)
    
    if name_node:
        # Use resolve_qualified_name to get clean names (e.g. Container instead of Container<T>)
        name = resolve_qualified_name(name_node, code_bytes)
        if name == "unknown":
            name = code_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8', errors='ignore').strip()
            
        # For functions, append parameters to distinguish overloads.
        # We recursively look for a parameter_list or a node with the 'parameters' field under 'node'.
        params = None
        def find_params_node(n):
            if n.type == "parameter_list": return n
            p_field = n.child_by_field_name("parameters")
            if p_field: return p_field
            for child in n.children:
                res = find_params_node(child)
                if res: return res
            return None

        if node.type in ["function_definition", "declaration", "method_declaration", "template_declaration", "function_declarator"]:
            # For template_declarations, we want the parameters of the INNER function/declaration
            target = node
            if node.type == "template_declaration":
                for child in reversed(node.children):
                    if child.type in ["function_definition", "declaration", "method_declaration", "function_declarator"]:
                        target = child
                        break
            
            # Robust recursive search for ANY parameter-like node
            def find_params_anywhere(p):
                if p.type in ["parameter_list", "parameters", "argument_list"]:
                    # In some C++ function pointer contexts, parameter_list might be deep
                    return p
                # Also check field
                f = p.child_by_field_name("parameters")
                if f: return f
                for child in p.children:
                    res = find_params_anywhere(child)
                    if res: return res
                return None
            
            params = find_params_anywhere(target)
            
        if params:
            param_str = code_bytes[params.start_byte:params.end_byte].decode('utf-8', errors='ignore').strip()
            name = f"{name}{param_str}"
            
        return name
    return "unknown"

def resolve_qualified_name(node, code_bytes: bytes) -> str:
    """Recursively resolve name for qualified identifiers, template types, etc."""
    if node.type in ["identifier", "field_identifier", "type_identifier", "namespace_identifier", "destructor_name"]:
        return code_bytes[node.start_byte:node.end_byte].decode("utf-8", "ignore")
    elif node.type == "qualified_identifier":
        parts = []
        for child in node.children:
            if child.type not in ["::", "comment"]:
                res = resolve_qualified_name(child, code_bytes)
                if res != "unknown" and res:
                    parts.append(res)
        return "::".join(parts) if parts else "unknown"
    elif node.type == "template_type":
        name_node = node.child_by_field_name("name")
        if name_node:
            return resolve_qualified_name(name_node, code_bytes)
        # Fallback to children search if field missing
        for child in node.children:
            if child.type in ["identifier", "type_identifier", "qualified_identifier"]:
                return resolve_qualified_name(child, code_bytes)
    elif node.type in ["function_declarator", "pointer_declarator", "reference_declarator"]:
        for child in node.children:
            if child.type not in ["(", ")", "*", "&", "comment"]:
                res = resolve_qualified_name(child, code_bytes)
                if res != "unknown": return res
    return "unknown"

def get_parent_scope_name(node, code_bytes: bytes) -> str:
    """Find the full qualified name of the containing scope(s)."""
    p = node.parent
    scopes = []
    # Language-specific container types
    container_types = [
        "class_specifier", "struct_specifier", "enum_specifier", "function_definition",
        "class_definition", # Python
        "class_declaration", "interface_declaration", "enum_declaration", "trait_declaration", "record_declaration", # Java, PHP, JS, TS
        "method_definition", "method_declaration", # JS, TS, PHP, Go
        "internal_module", # TS namespace
        "struct_item", "enum_item", "trait_item", "mod_item", "function_item", # Rust
        "type_declaration", # Go
        "function_declaration", # Lua, Go, PHP
    ]
    
    while p:
        # Debug: print(f"  Climbing: {p.type}")
        is_scope = False
        if p.type in container_types:
            is_scope = True
        elif p.type in ["class", "interface", "struct", "enum", "module"]: # Generic fallbacks
            is_scope = True
            
        if is_scope:
            name = "unknown"
            if p.type in ["function_definition", "function_declaration", "method_definition", "method_declaration", "function_item"]:
                name = extract_entity_name(p, code_bytes)
                if "(" in name: name = name.split("(")[0]
                if ":" in name and "::" not in name:
                    name = name.replace(":", "::")
            else:
                name_node = p.child_by_field_name("name")
                if not name_node:
                    # Look for first identifier-like child
                    for child in p.children:
                        if child.type in ["identifier", "type_identifier", "field_identifier", "name"]:
                            name_node = child
                            break
                if name_node:
                    name = code_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8", "ignore")
            
            if name != "unknown" and name:
                # Avoid self-parenting if extract_entity_name for parent returns child name (shouldn't happen but safe)
                if not scopes or scopes[-1] != name:
                    scopes.append(name)
        p = p.parent
    if not scopes:
        return "global"
    return "::".join(reversed(scopes))

def extract_code_entities(code_bytes: bytes, ext: str) -> list:
    if ext == ".py":
        lang = PY_LANGUAGE
        query_scm = "(function_definition) @function (class_definition) @type"
    elif ext in [".cpp", ".hpp", ".h", ".cc", ".cxx"]:
        lang = CPP_LANGUAGE
        query_scm = """
            (template_declaration) @template
            (function_definition) @function
            (class_specifier) @type
            (struct_specifier) @type
            (enum_specifier) @type
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

    # 1. Group captures by their 'effective' logical node (e.g. the class/function inside templates)
    entities_by_effective = {} # effective_node_id -> (outer_node, effective_node, capture_name)
    
    for node, capture_name in all_captures:
        effective_node = node
        if node.type == "template_declaration":
            curr = node
            while True:
                inner = None
                for child in reversed(curr.children):
                    if child.type not in ["template", "template_parameter_list", "<", ">", ",", "comment", ";"]:
                        inner = child
                        break
                if inner and inner.type == "template_declaration":
                    curr = inner
                else:
                    if inner: effective_node = inner
                    break
                    
        eid = (effective_node.id, effective_node.start_byte, effective_node.end_byte)
        curr_size = node.end_byte - node.start_byte
        if eid not in entities_by_effective:
            entities_by_effective[eid] = (node, effective_node, capture_name)
        else:
            prev_node, _, _ = entities_by_effective[eid]
            prev_size = prev_node.end_byte - prev_node.start_byte
            if curr_size > prev_size:
                entities_by_effective[eid] = (node, effective_node, capture_name)

    # 2. Extract Names and Deduplicate by Full Name + Logical Type
    final_entities_map = {} # (full_name, logical_type) -> (outer_node, effective_node, capture_name)
    
    for eid, (outer_node, effective_node, capture_name) in entities_by_effective.items():
        base_name = extract_entity_name(effective_node, code_bytes)
        if base_name == "unknown": continue
        
        scope = get_parent_scope_name(effective_node, code_bytes)
        # Construct full qualified name if not already qualified
        if "::" not in base_name and scope != "global":
            full_name = f"{scope}::{base_name}"
        else:
            full_name = base_name
            
        is_func = "function" in capture_name or effective_node.type in ["function_definition", "declaration", "method_declaration"]
        logical_type = "function" if is_func else "type"
        
        key = (full_name, logical_type)
        curr_size = outer_node.end_byte - outer_node.start_byte
        
        if key in final_entities_map:
            prev_node, _, _ = final_entities_map[key]
            prev_size = prev_node.end_byte - prev_node.start_byte
            # If same name/type, prefer the larger node (definition over declaration)
            if curr_size > prev_size:
                final_entities_map[key] = (outer_node, effective_node, capture_name)
        else:
            final_entities_map[key] = (outer_node, effective_node, capture_name)

    entities = []
    # 3. Convert map back to final list
    for (full_name, _), (outer_node, effective_node, capture_name) in final_entities_map.items():
        name = full_name
        current_start = outer_node.start_byte
        actual_start_line = outer_node.start_point[0] + 1
        prev = outer_node.prev_sibling
        while prev and prev.type in ["comment", "line_comment", "block_comment"]:
            current_start = prev.start_byte
            actual_start_line = prev.start_point[0] + 1
            prev = prev.prev_sibling
        
        code = code_bytes[current_start:outer_node.end_byte].decode('utf-8', errors='ignore')
        entities.append({
            "name": name,
            "start_line": actual_start_line,
            "end_line": outer_node.end_point[0] + 1,
            "code": code,
            "type": capture_name
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
