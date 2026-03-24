import os
import json
import hashlib
from pathlib import Path
import tempfile
import git
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import openai

# Use swh.model if possible
try:
    from swh.model.ident import compute_identifier, ObjectType
    SWH_MODEL_AVAILABLE = True
except ImportError:
    SWH_MODEL_AVAILABLE = False

REPO_URL = "https://github.com/aboffa/CoCo-trie"
# As in the user's example, we use a single slash after the protocol for the origin URL part of the SWHID
SWH_ORIGIN = REPO_URL.replace("https://", "https:/") 

FAISS_INDEX_PATH = "event_horizon.index"
EMBEDDING_DIM = 384 # all-MiniLM-L6-v2 dim

def get_swhid_content_hash(content: bytes) -> str:
    """
    Computes the SWHID hash for content. 
    Matches swh identify: sha1("blob " + length + "\0" + content)
    """
    if SWH_MODEL_AVAILABLE:
        # compute_identifier returns a hash string or object
        res = compute_identifier(ObjectType.CONTENT, {"data": content})
        return str(res)
    else:
        # Manual fallback matching SWH spec
        header = f"blob {len(content)}\0".encode()
        return hashlib.sha1(header + content).hexdigest()

def extract_functions_llm(code: str, filepath: str) -> list:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(f"⚠️ No OPENAI_API_KEY set. Falling back to heuristic chunking for {filepath}")
        return extract_functions_heuristic(code, filepath)
    
    client = openai.Client()
    # Refined prompt for strict function extraction including comments/docstrings
    prompt = (
        "You are an expert code analyst. Extract all standalone functions and methods from the provided source code. "
        "For each function, identify the EXACT start line (including its leading comments/docstrings) "
        "and the EXACT end line (the line containing the final closing brace or return statement). "
        "Exclude global variables, include guards, pragmas, and top-level definitions that are not functions. "
        "Return ONLY a valid JSON object with a single 'functions' key mapping to a list of objects. "
        "Each object must have: 'name' (string), 'start_line' (int, 1-indexed), 'end_line' (int, 1-indexed).\n\n"
        f"File: {filepath}\nCode:\n{code}"
    )
    try:
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL_NAME", "gpt-4o"), # Prefer gpt-4o for precise extraction
            messages=[{"role": "system", "content": "You are a code parsing assistant."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("functions", [])
    except Exception as e:
        print(f"⚠️ LLM extraction failed: {e}. Falling back to heuristic.")
        return extract_functions_heuristic(code, filepath)

def extract_functions_heuristic(code: str, filepath: str) -> list:
    # Improved heuristic: try to find common function patterns if LLM fails
    lines = code.splitlines()
    if len(lines) < 100:
        return [{"name": "entire_file", "start_line": 1, "end_line": len(lines)}]
    chunks = []
    chunk_size = 50
    for i in range(0, len(lines), chunk_size):
        chunks.append({
            "name": f"chunk_{i//chunk_size}",
            "start_line": i + 1,
            "end_line": min(i + chunk_size, len(lines))
        })
    return chunks

def build_pipeline():
    print(f"== Event Horizon: Semantic Code Search Build Pipeline ==")
    print(f"swh.model library available: {SWH_MODEL_AVAILABLE}")
    
    # 1. Clone Target Repo
    print(f"Cloning repository: {REPO_URL}")
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "CoCo-trie"
        try:
            # Standard clone, we will handle normalization in memory
            git.Repo.clone_from(REPO_URL, repo_path)
        except Exception as e:
            print(f"Clone failed: {e}")
            return
            
        print("Extracting and identifying functions...")
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
                        
                        # Normalize to LF for hashing (standard for SWH/Git)
                        text_lf = raw_content.replace(b"\r\n", b"\n")
                        swhid_hash = get_swhid_content_hash(text_lf)
                        
                        text_content = text_lf.decode('utf-8')
                    except Exception:
                        continue
                    
                    extracted = extract_functions_llm(text_content, str(filepath))
                    lines = text_content.splitlines()
                    
                    for fn in extracted:
                        start = max(1, fn.get("start_line", 1))
                        end = min(len(lines), fn.get("end_line", len(lines)))
                        
                        func_code = "\n".join(lines[start-1:end])
                        if not func_code.strip():
                            continue
                            
                        func_hash = hashlib.md5(func_code.encode()).hexdigest()
                        
                        # Corrected SWHID format: swh:1:cnt:HASH;origin=https:/github.com/...;lines=S-E
                        swhid = f"swh:1:cnt:{swhid_hash};origin={SWH_ORIGIN};lines={start}-{end}/"
                        
                        functions.append({
                            "id": func_hash,
                            "name": fn.get("name", "unknown"),
                            "code": func_code,
                            "swhid": swhid,
                            "filepath": str(filepath.relative_to(repo_path)).replace("\\", "/")
                        })
                        
    unique_funcs = {f["id"]: f for f in functions}
    functions = list(unique_funcs.values())
    print(f"Extracted {len(functions)} unique functions.")
    
    with open("functions.json", "w", encoding="utf-8") as f:
        json.dump(functions, f, indent=2)
        
    if not functions:
        return
        
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode([f["code"] for f in functions])
    
    print(f"Building FAISS index...")
    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index.add(np.array(embeddings).astype('float32'))
    faiss.write_index(index, FAISS_INDEX_PATH)
    
    print("✅ Build pipeline complete with corrected SWHIDs.")

if __name__ == "__main__":
    build_pipeline()
