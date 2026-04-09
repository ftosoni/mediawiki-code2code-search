import faiss
import os
import numpy as np

WORKSPACE = r"c:\Users\franc\Documents\GitHub\mediawiki-code2code-search"
INDEX_PATH = os.path.join(WORKSPACE, "backend", "mediawiki.index")
MISSING_IDS_PATH = os.path.join(WORKSPACE, "tmp", "missing_ids.txt")

def patch_index():
    if not os.path.exists(INDEX_PATH):
        print(f"Error: {INDEX_PATH} not found.")
        return

    print(f"Reading index from {INDEX_PATH}...")
    index = faiss.read_index(INDEX_PATH)
    print(f"Current index size: {index.ntotal}")

    print("Reading missing IDs...")
    with open(MISSING_IDS_PATH, "r") as f:
        missing_ids = [int(line.strip()) for line in f]
    
    print(f"Removing {len(missing_ids)} IDs from index...")
    # IndexIVFPQ supports remove_ids
    ids_to_remove = np.array(missing_ids).astype('int64')
    
    try:
        n_removed = index.remove_ids(faiss.IDSelectorBatch(ids_to_remove))
        print(f"Successfully removed {n_removed} IDs.")
    except Exception as e:
        print(f"Error removing IDs: {e}")
        print("Falling back to manual reconstruction (if possible)...")
        # If remove_ids is not supported by this index type, we might need a different approach.
        # But IndexIVFPQ usually supports it.
        return

    new_path = INDEX_PATH # Overwrite
    faiss.write_index(index, new_path)
    print(f"Updated index saved to {new_path}")
    print(f"New index size: {index.ntotal}")

if __name__ == "__main__":
    patch_index()
