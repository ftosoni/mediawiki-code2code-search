import os
# Disable symlinks for HF on Windows if not admin
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
from transformers import AutoModel

try:
    print("Attempting to load Jina v2-code-en model...")
    model = AutoModel.from_pretrained("jinaai/jina-embeddings-v2-code-en", trust_remote_code=True)
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
