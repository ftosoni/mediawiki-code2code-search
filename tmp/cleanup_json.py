import json
import os

WORKSPACE = r"c:\Users\franc\Documents\GitHub\mediawiki-code2code-search"
RAW_JSON = os.path.join(WORKSPACE, "backend", "raw_functions.json")
FUNCTIONS_JSON = os.path.join(WORKSPACE, "backend", "functions.json")

def cleanup_json(path):
    if not os.path.exists(path):
        print(f"Skipping {path} (not found).")
        return

    print(f"Processing {path}...")
    repo_name = 'easypage-ai-deletion_scheduled-3364'
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    count_before = len(data)
    # Check what key is used for repo name. In raw_functions.json it's 'repo_name'.
    # I'll check a sample.
    if count_before > 0:
        first = data[0]
        key = 'repo_name' if 'repo_name' in first else None
        if not key:
            print(f"Warning: Could not find repo key in {path}. Sample: {list(first.keys())}")
            return
            
        data = [item for item in data if item.get(key) != repo_name]
    
    count_after = len(data)
    print(f"  Rows before: {count_before}")
    print(f"  Rows after: {count_after}")
    
    if count_before != count_after:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Updated {path}")
    else:
        print(f"No changes needed for {path}")

if __name__ == "__main__":
    cleanup_json(RAW_JSON)
    cleanup_json(FUNCTIONS_JSON)
