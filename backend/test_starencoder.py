import os
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
from transformers import AutoModel, AutoTokenizer

model_id = "bigcode/starencoder"
try:
    print(f"Attempting to load {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModel.from_pretrained(model_id)
    print(f"✅ {model_id} loaded successfully.")
except Exception as e:
    print(f"❌ Failed to load {model_id}: {e}")
