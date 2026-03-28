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
import re
from dotenv import load_dotenv

# Tree-sitter imports (0.23+ API)
import tree_sitter
import tree_sitter_python
import tree_sitter_cpp
import tree_sitter_c

# Initialize Languages
PY_LANGUAGE = tree_sitter.Language(tree_sitter_python.language())
CPP_LANGUAGE = tree_sitter.Language(tree_sitter_cpp.language())
C_LANGUAGE = tree_sitter.Language(tree_sitter_c.language())

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

FAISS_INDEX_PATH = "event_horizon.index"
EMBEDDING_DIM = 896 # Jina 0.5B dim
DEBUG_LIMIT = 256   # Process a set amount of functions (0 for no limit)

def get_swhid_content_hash(content: bytes) -> str:
    if SWH_MODEL_AVAILABLE:
        res = compute_identifier(ObjectType.CONTENT, {"data": content})
        return str(res)
    else:
        header = f"blob {len(content)}\0".encode()
        return hashlib.sha1(header + content).hexdigest()

def extract_functions_treesitter(code_bytes: bytes, ext: str) -> list:
    """
    High-precision AST-based function extraction using Tree-sitter.
    Includes preceding comments/docstrings by traversing siblings.
    """
    if ext == ".py":
        lang = PY_LANGUAGE
        query_scm = "(function_definition) @function"
    elif ext in [".cpp", ".hpp", ".h"]:
        lang = CPP_LANGUAGE
        # Comprehensive C++ patterns
        query_scm = "(function_definition) @function (template_declaration) @function"
    elif ext == ".c":
        lang = C_LANGUAGE
        query_scm = "(function_definition) @function"
    else:
        return []

    try:
        parser = tree_sitter.Parser(lang)
        tree = parser.parse(code_bytes)
        query = lang.query(query_scm)
        captures = query.captures(tree.root_node)
    except Exception as e:
        # Fallback for headers that might be C or C++
        if ext == ".h":
             try:
                 lang = C_LANGUAGE
                 parser = tree_sitter.Parser(lang)
                 tree = parser.parse(code_bytes)
                 query = lang.query("(function_definition) @function")
                 captures = query.captures(tree.root_node)
             except Exception:
                 return []
        else:
            raise e
    
    # Normalize captures to a list of nodes
    if isinstance(captures, dict):
        all_nodes = []
        for nodes in captures.values():
            all_nodes.extend(nodes)
        captures = all_nodes

    functions = []
    seen_nodes = set()
    
    for capture in captures:
        # Robustly extract Node from capture (can be Node or (Node, tag))
        if isinstance(capture, tuple) and len(capture) > 0:
            node = capture[0]
        elif hasattr(capture, 'start_byte'):
            node = capture
        else:
            continue
            
        node_key = (node.start_byte, node.end_byte)
        if node_key in seen_nodes: continue
        seen_nodes.add(node_key)
        
        # Start/End points
        start_byte = node.start_byte
        end_byte = node.end_byte
        start_line = node.start_point[0] + 1
        
        # Walk backward to include comments/docstrings
        current_start = start_byte
        actual_start_line = start_line
        
        prev = node.prev_sibling
        while prev and prev.type in ["comment", "line_comment", "block_comment"]:
            current_start = prev.start_byte
            actual_start_line = prev.start_point[0] + 1
            prev = prev.prev_sibling
            
        func_code = code_bytes[current_start:end_byte].decode('utf-8', errors='ignore')
        
        # Extract function name (heuristic within node)
        name = "unknown"
        for child in node.children:
            if child.type in ["identifier", "field_identifier"]:
                name = code_bytes[child.start_byte:child.end_byte].decode('utf-8', errors='ignore')
                break
        
        functions.append({
            "name": name,
            "start_line": actual_start_line,
            "end_line": node.end_point[0] + 1,
            "code": func_code
        })
        
    return functions

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
    valid_exts = {".c", ".cpp", ".h", ".hpp", ".py"}
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
                    
                    extracted = extract_functions_treesitter(text_lf, ext)
                    print(f"  Extracted {len(extracted)} functions.")
                    
                    for fn in extracted:
                        func_code = fn["code"]
                        if not func_code.strip(): continue
                            
                        # Unique ID based on code content
                        func_hash = hashlib.md5(func_code.encode()).hexdigest()
                        
                        # SWHID format: swh:1:cnt:HASH;origin=URL;lines=S-E
                        swhid = f"swh:1:cnt:{swhid_hash};origin={SWH_ORIGIN};lines={fn['start_line']}-{fn['end_line']}/"
                        
                        functions.append({
                            "id": func_hash,
                            "name": fn["name"],
                            "code": func_code,
                            "swhid": swhid,
                            "filepath": str(filepath.relative_to(repo_path)).replace("\\", "/")
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
        
    # Sort by code length to optimize batching performance (minimizes padding overhead)
    functions.sort(key=lambda x: len(x["code"]))
    
    with open("functions.json", "w", encoding="utf-8") as f:
        json.dump(functions, f, indent=2)
        
    print(f"\nVectorizing {len(functions)} unique functions with Jina (896D)...")
    
    code_snippets = [f["code"] for f in functions]
    
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
