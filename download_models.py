import os
from huggingface_hub import snapshot_download

# Standardise Paths (Script Relative)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def download_model(repo_id, folder_name):
    print(f"--- Downloading {repo_id} ({folder_name}) ---")
    save_path = os.path.join(MODELS_DIR, folder_name)
    
    # Use snapshot_download to get ALL files including custom modeling.py
    snapshot_download(
        repo_id=repo_id, 
        local_dir=save_path, 
        local_dir_use_symlinks=False, # Copy files for easy transfer
        ignore_patterns=["onnx/*", "*.onnx"] # Skip heavy ONNX weights
    )
    print(f"✅ Successfully downloaded to {save_path}")

if __name__ == "__main__":
    # 1. Recall model (Bi-Encoder)
    download_model("jinaai/jina-code-embeddings-0.5b", "jina-embeddings")
    
    # 2. Reranker model (Cross-Encoder)
    download_model("jinaai/jina-reranker-v2-base-multilingual", "jina-reranker")
    
    print("\n✅ All models successfully saved in the 'models/' directory.")
    print("You can now transfer this folder to your Toolforge project root.")
