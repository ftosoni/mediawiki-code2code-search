import os
import json
import hashlib
from pathlib import Path
import tempfile
import git
import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
import requests
import re
from dotenv import load_dotenv

# Tree-sitter imports (0.23+ API)
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

# Load local environment variables
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

# Use swh.model if possible
try:
    from swh.model.ident import compute_identifier, ObjectType
    SWH_MODEL_AVAILABLE = True
except ImportError:
    SWH_MODEL_AVAILABLE = False

REPO_URL = "https://github.com/aboffa/CoCo-trie"
SWH_ORIGIN = REPO_URL.replace("https://", "https:/") 

FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "mediawiki.index")
EMBEDDING_DIM = 896 # Jina 0.5B dim
DEBUG_LIMIT = 256   # Process a set amount of functions (0 for no limit)

# Cache for SHA1 Git -> Standard SHA1
SWH_SHA1_CACHE = {}

def get_sha1_from_swh(sha1_git: str) -> str:
    """Fetch standard SHA1 from SWH API given a sha1_git."""
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

def get_swhid_content_hash(content: bytes) -> str:
    if SWH_MODEL_AVAILABLE:
        res = compute_identifier(ObjectType.CONTENT, {"data": content})
        return str(res)
    else:
        header = f"blob {len(content)}\0".encode()
        return hashlib.sha1(header + content).hexdigest()

def extract_code_entities(code_bytes: bytes, ext: str) -> list:
    """
    High-precision AST-based extraction of functions and types using Tree-sitter.
    Categorizes entities as 'function' or 'type' (classes, structs, interfaces).
    """
    if ext == ".py":
        lang = PY_LANGUAGE
        query_scm = "(function_definition) @function (class_definition) @type"
    elif ext in [".cpp", ".hpp", ".h", ".cc", ".cxx"]:
        lang = CPP_LANGUAGE
        query_scm = """
            ; Template-wrapped entities
            (template_declaration (function_definition)) @template_function
            (template_declaration [(class_specifier) (struct_specifier) (enum_specifier) (alias_declaration)]) @template_type
            
            ; Non-template entities (also captures methods and inner components)
            (function_definition) @function
            (class_specifier) @type
            (struct_specifier) @type
            (enum_specifier) @type
            (alias_declaration) @type
        """
        # Ensure category mapping is available for filtering
        category_map = {
            "template_function": "function",
            "template_type": "type",
            "function": "function",
            "type": "type"
        }
    elif ext == ".c":
        lang = C_LANGUAGE
        query_scm = "(function_definition) @function (struct_specifier) @type (union_specifier) @type (enum_specifier) @type"
    elif ext == ".php":
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
    except Exception as e:
        # Fallback for headers that might be C or C++
        if ext == ".h":
             try:
                 lang = C_LANGUAGE
                 parser = tree_sitter.Parser(lang)
                 tree = parser.parse(code_bytes)
                 query = tree_sitter.Query(lang, "(function_definition) @function (struct_specifier) @type (enum_specifier) @type")
                 cursor = tree_sitter.QueryCursor(query)
                 captures_dict = cursor.captures(tree.root_node)
             except Exception:
                 return []
        else:
            print(f"  Tree-sitter error for {ext}: {e}")
            return []
    
    # Normalize 0.23+ API dictionary-style captures to flat list of (Node, entity_type)
    all_captures = []
    for entity_type, nodes in captures_dict.items():
        for node in nodes:
            all_captures.append((node, entity_type))

    # Sort captures by range size (largest first) to prioritize template wrappers
    # and outer classes over inner ones of the same type.
    all_captures.sort(key=lambda x: (x[0].end_byte - x[0].start_byte), reverse=True)

    # Redundancy filtering: for each entity_type, skip nodes that are already
    # contained within a larger node of the SAME logical type (e.g. template class vs class).
    final_nodes = []
    # Map high-level categories for overlap checks
    category_map = {
        "template_function": "function",
        "template_type": "type",
        "function": "function",
        "type": "type"
    }
    # (start, end, name) -> logical_type
    covered_ranges = {"function": [], "type": []}
    
    for node, entity_type in all_captures:
        node_start, node_end = node.start_byte, node.end_byte
        name = extract_entity_name(node, code_bytes)
        
        # Determine logical category (e.g. template_type and type share the 'type' category)
        logical_cat = category_map.get(entity_type, entity_type)
        
        # Check if this node is already fully covered by a larger node of the SAME logical type
        # AND shares the same name (redundant template wrapper vs body)
        is_covered = False
        for (c_start, c_end, c_name) in covered_ranges.get(logical_cat, []):
            if node_start >= c_start and node_end <= c_end:
                if name == c_name or name == "unknown":
                    is_covered = True
                    break
        
        if not is_covered:
            final_nodes.append((node, entity_type))
            if logical_cat not in covered_ranges:
                covered_ranges[logical_cat] = []
            covered_ranges[logical_cat].append((node_start, node_end, name))

    functions = []
    for node, entity_type in final_nodes:
        # Extract name using helper
        name = extract_entity_name(node, code_bytes)
        
        # Walk backward to include comments/docstrings
        current_start = node.start_byte
        actual_start_line = node.start_point[0] + 1
        
        prev = node.prev_sibling
        while prev and prev.type in ["comment", "line_comment", "block_comment"]:
            current_start = prev.start_byte
            actual_start_line = prev.start_point[0] + 1
            prev = prev.prev_sibling
            
        func_code = code_bytes[current_start:node.end_byte].decode('utf-8', errors='ignore')
        
        functions.append({
            "name": name,
            "start_line": actual_start_line,
            "end_line": node.end_point[0] + 1,
            "code": func_code,
            "type": entity_type
        })
        
    return functions


def extract_entity_name(node, code_bytes: bytes) -> str:
    """Extract name from AST node"""
    # Handle template_declaration specially: we want the name of the template body,
    # not the template parameters.
    if node.type == "template_declaration":
        # Search in the child that isn't the 'template' keyword or parameter list
        for child in reversed(node.children):
            if child.type not in ["template", "template_parameter_list", "<", ">", ",", "comment", ";"]:
                name = extract_entity_name(child, code_bytes)
                if name and name != "unknown":
                    return name

    # Try named 'name' field first
    name_node = node.child_by_field_name("name")
    if not name_node:
        # Heuristic: find first identifier in descendants
        def find_name(n):
            if n.type in ["identifier", "field_identifier", "type_identifier"]:
                return n
            # Search children, but prioritize 'field_identifier' in case of class nodes
            for child in n.children:
                found = find_name(child)
                if found:
                    return found
            return None
        name_node = find_name(node)
    
    if name_node:
        return code_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8', errors='ignore')
    
    return "unknown"

def build_pipeline():
    print(f"== Event Horizon: Semantic Code Search Build Pipeline (Local-First Edition) ==")
    
    # Use HF_TOKEN for authentication (faster downloads/API checks)
    print(f"Initialising Jina Code Embeddings (jinaai/jina-code-embeddings-0.5b)...")
    model = SentenceTransformer(
        "jinaai/jina-code-embeddings-0.5b", 
        trust_remote_code=True, 
        device="cpu",
        use_auth_token=HF_TOKEN
    )
    # Cap sequence length aggressively for initial diagnosis (default 32k context is too slow for CPU)
    # 512 is common for embeddings and should be very fast even on CPU.
    model.max_seq_length = 512

    repo_path = Path("CoCo-trie")
    if not repo_path.exists():
        print(f"Cloning {REPO_URL}...")
        git.Repo.clone_from(REPO_URL, repo_path)
    else:
        print(f"Using local repository: {repo_path}")
            
    print("Segmenting functions using Tree-sitter AST...")
    functions = []
    valid_exts = {
        ".c", ".cpp", ".h", ".hpp", ".cc", ".cxx",
        ".py", ".php", ".js", ".ts", ".tsx", ".mts", ".cts",
        ".lua", ".go", ".java", ".rs"
    }
    for root, _, files in os.walk(repo_path):
        if ".git" in root: continue
        for file in files:
            ext = Path(file).suffix
            if ext in valid_exts:
                filepath = Path(root) / file
                print(f"Processing {filepath}...")
                try:
                    with open(filepath, "rb") as f:
                        raw_content = f.read()
                    
                    text_lf = raw_content.replace(b"\r\n", b"\n")
                    swhid_hash = get_swhid_content_hash(text_lf)
                    
                    extracted = extract_code_entities(text_lf, ext)
                    print(f"  Extracted {len(extracted)} entities.")
                    
                    for ent in extracted:
                        func_code = ent["code"]
                        if not func_code.strip(): continue
                            
                        # Unique ID based on code content
                        func_hash = hashlib.md5(func_code.encode()).hexdigest()
                        
                        # Look up standard SHA1 for S3 access
                        sha1 = get_sha1_from_swh(swhid_hash)
                        
                        # SWHID format: swh:1:cnt:HASH;origin=URL;lines=S-E
                        swhid = f"swh:1:cnt:{swhid_hash};origin={SWH_ORIGIN};lines={ent['start_line']}-{ent['end_line']}/"
                        
                        functions.append({
                            "id": func_hash,
                            "swhid": swhid,
                            "sha1": sha1,
                            "filepath": str(filepath.relative_to(repo_path)).replace("\\", "/"),
                            "name": ent["name"],
                            "type": ent["type"],
                            "code_for_embedding": func_code # Temporary field for vectorization
                        })
                except Exception as e:
                    print(f"  Failed to process {file}: {e}")
                        
    unique_funcs = {f["id"]: f for f in functions}
    functions = list(unique_funcs.values())
    
    if DEBUG_LIMIT :
        print(f"DEBUG MODE: Limiting to first {DEBUG_LIMIT} functions.")
        functions = functions[:DEBUG_LIMIT]
        
    print(f"Extracted {len(functions)} unique functions via structural segmentation.")
    
    if not functions:
        print("No functions extracted. Pipeline aborted.")
        return
        
    # Sort by code length to optimize batching performance
    functions.sort(key=lambda x: len(x["code_for_embedding"]))
    
    # We SAVE a version WITHOUT the code for production search!
    # This is the key RAM optimization.
    functions_meta_only = []
    for f in functions:
        meta = f.copy()
        code_text = meta.pop("code_for_embedding") # Extract for embedding
        functions_meta_only.append(meta)
    
    meta_path = os.path.join(os.path.dirname(__file__), "functions.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(functions_meta_only, f, indent=2)
        
    print(f"\nVectorizing {len(functions)} unique functions with Jina (896D)...")
    
    code_snippets = [f["code_for_embedding"] for f in functions]
    
    # Detailed diagnostic logging
    avg_len = sum(len(s) for s in code_snippets) / len(code_snippets) if code_snippets else 0
    max_len = max(len(s) for s in code_snippets) if code_snippets else 0
    print(f"Encoding snippets (Avg: {avg_len:.1f}, Max: {max_len} chars)...")

    embeddings = model.encode(
        code_snippets, 
        batch_size=1,           # Forced batch_size=1 to ensure progress updates for every snippet
        show_progress_bar=True, 
        normalize_embeddings=True
    )
    
    print(f"\nInitialising FAISS IndexIVFPQ (Disk-ready)...")
    # nlist should be less than the number of points for training
    nlist = min(100, len(functions))
    quantizer = faiss.IndexFlatL2(EMBEDDING_DIM)
    index = faiss.IndexIVFPQ(quantizer, EMBEDDING_DIM, nlist, 32, 8)
    
    print("Training IVF index on extracted embeddings...")
    index.train(embeddings.astype('float32'))
    
    print("Adding vectors to index...")
    index.add(embeddings.astype('float32'))
    
    faiss.write_index(index, FAISS_INDEX_PATH)
    
    print("✅ Build pipeline complete. Local-first architecture prioritised.")

if __name__ == "__main__":
    build_pipeline()
