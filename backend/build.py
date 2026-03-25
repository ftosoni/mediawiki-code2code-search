import os
import json
import hashlib
from pathlib import Path
import tempfile
import git
import torch
from transformers import AutoModel, AutoTokenizer
import faiss
import numpy as np
import re
from dotenv import load_dotenv

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
EMBEDDING_DIM = 768 # UniXcoder dim

def get_swhid_content_hash(content: bytes) -> str:
    if SWH_MODEL_AVAILABLE:
        res = compute_identifier(ObjectType.CONTENT, {"data": content})
        return str(res)
    else:
        header = f"blob {len(content)}\0".encode()
        return hashlib.sha1(header + content).hexdigest()

def extract_functions_heuristic(code: str, ext: str) -> list:
    """
    Robust heuristic-based function extraction for Python and C/C++.
    Includes preceding comments/docstrings.
    """
    lines = code.splitlines()
    functions = []
    
    if ext == ".py":
        # Python: find 'def name(...):'
        pattern = re.compile(r"^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
    else:
        # C/C++: optimized signature matching (fast, avoid backtracking)
        # Matches: [template] type [class::]name(args)
        pattern = re.compile(r"^\s*(?:[\w\d\*\&\:<> ]+\s+)+([a-zA-Z_]\w*)\s*\([^\)]*\)\s*(?:const)?\s*(?:\{|$)")

    for i, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            fn_name = match.group(1)
            # Skip common keywords
            if fn_name in ["if", "while", "for", "switch", "return", "catch", "template"]: continue
            
            start_line = i + 1
            
            # Walk backward to collect comments
            comments = []
            j = i - 1
            while j >= 0:
                prev_line = lines[j].strip()
                if not prev_line: 
                    j -= 1
                    continue
                if ext == ".py":
                    if prev_line.startswith("#"):
                        comments.insert(0, lines[j])
                        j -= 1
                    else: break
                else: # C/C++
                    if prev_line.startswith("//") or prev_line.startswith("/*") or prev_line.endswith("*/"):
                        comments.insert(0, lines[j])
                        j -= 1
                    else: break
            
            # end_line detection
            end_line = len(lines)
            if ext == ".py":
                for k in range(i + 1, len(lines)):
                    # Get indent of 'def' line
                    indent = len(line) - len(line.lstrip())
                    if lines[k].strip() and (len(lines[k]) - len(lines[k].lstrip())) <= indent:
                        end_line = k
                        break
            else:
                # Brace counting for C/C++
                brace_count = 0
                started = False
                for k in range(i, len(lines)):
                    brace_count += lines[k].count("{") - lines[k].count("}")
                    if "{" in lines[k]: started = True
                    if started and brace_count <= 0:
                        end_line = k + 1
                        break
            
            func_code = "\n".join(comments + lines[i:end_line])
            functions.append({
                "name": fn_name,
                "start_line": start_line - len(comments),
                "end_line": end_line,
                "code": func_code
            })
            
    return functions

def build_pipeline():
    print(f"== Event Horizon: Semantic Code Search Build Pipeline (Local-First Edition) ==")
    print(f"SWH.model library available: {SWH_MODEL_AVAILABLE}")
    
    print(f"Initialising UniXcoder (microsoft/unixcoder-base)...")
    tokenizer = AutoTokenizer.from_pretrained("microsoft/unixcoder-base")
    model = AutoModel.from_pretrained("microsoft/unixcoder-base").to("cpu")
    model.eval()

    print(f"Cloning repository: {REPO_URL}")
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "CoCo-trie"
        try:
            git.Repo.clone_from(REPO_URL, repo_path)
        except Exception as e:
            print(f"Clone failed: {e}")
            return
            
        print("Segmenting functions using Tree-sitter AST...")
        functions = []
        valid_exts = {".c", ".cpp", ".h", ".hpp", ".py"}
        for root, _, files in os.walk(repo_path):
            if ".git" in root: continue
            for file in files:
                ext = Path(file).suffix
                if ext in valid_exts:
                    filepath = Path(root) / file
                    try:
                        with open(filepath, "rb") as f:
                            raw_content = f.read()
                        
                        text_lf = raw_content.replace(b"\r\n", b"\n")
                        swhid_hash = get_swhid_content_hash(text_lf)
                        text_content = text_lf.decode('utf-8')
                    except Exception:
                        continue
                    
                    extracted = extract_functions_heuristic(text_content, ext)
                    for fn in extracted:
                        func_code = fn["code"]
                        if not func_code.strip(): continue
                            
                        # Unique ID based on code content
                        func_hash = hashlib.md5(func_code.encode()).hexdigest()
                        
                        # SWHID format: swh:1:cnt:HASH;origin=https:/github.com/...;lines=S-E
                        swhid = f"swh:1:cnt:{swhid_hash};origin={SWH_ORIGIN};lines={fn['start_line']}-{fn['end_line']}/"
                        
                        functions.append({
                            "id": func_hash,
                            "name": fn["name"],
                            "code": func_code,
                            "swhid": swhid,
                            "filepath": str(filepath.relative_to(repo_path)).replace("\\", "/")
                        })
                        
    unique_funcs = {f["id"]: f for f in functions}
    functions = list(unique_funcs.values())
    print(f"Extracted {len(functions)} unique functions via structural segmentation.")
    
    with open("functions.json", "w", encoding="utf-8") as f:
        json.dump(functions, f, indent=2)
        
    if not functions:
        print("No functions extracted. Pipeline aborted.")
        return
        
    print(f"Vectorising {len(functions)} functions with Jina Embeddings (768D)...")
    
    all_embeddings = []
    batch_size = 16
    for i in range(0, len(functions), batch_size):
        batch = functions[i:i+batch_size]
        batch_code = [f["code"] for f in batch]
        
        with torch.no_grad():
            inputs = tokenizer(batch_code, padding=True, truncation=True, return_tensors='pt', max_length=512)
            outputs = model(**inputs)
            # UniXcoder representation: use the hidden state of the first token (<s>)
            embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            all_embeddings.append(embeddings)
        print(f"Progress: {min(i+batch_size, len(functions))}/{len(functions)}", end="\r")
    
    embeddings = np.vstack(all_embeddings)
    
    print(f"\nInitialising FAISS index...")
    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index.add(np.array(embeddings).astype('float32'))
    faiss.write_index(index, FAISS_INDEX_PATH)
    
    print("✅ Build pipeline complete. Local-first architecture prioritised.")

if __name__ == "__main__":
    build_pipeline()

