import os
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer

# Standardise Paths (Script Relative)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

os.makedirs(MODELS_DIR, exist_ok=True)

def download_bi_encoder():
    print("--- Downloading Jina Embeddings (Bi-Encoder) ---")
    model_path = os.path.join(MODELS_DIR, "jina-embeddings")
    bi_model = SentenceTransformer("jinaai/jina-code-embeddings-0.5b", trust_remote_code=True)
    bi_model.save(model_path)
    print(f"Bi-Encoder saved to {model_path}")

def download_reranker():
    print("--- Downloading Jina Reranker v3 (Cross-Encoder) ---")
    model_name = "jinaai/jina-reranker-v3"
    model_path = os.path.join(MODELS_DIR, "jina-reranker")
    
    print("Fetching Reranker model weights...")
    rerank_model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
    print("Fetching Reranker tokenizer...")
    rerank_tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    rerank_model.save_pretrained(model_path)
    rerank_tokenizer.save_pretrained(model_path)
    print(f"Reranker saved to {model_path}")

if __name__ == "__main__":
    download_bi_encoder()
    download_reranker()
    print("\n✅ All models successfully saved in 'models/' directory.")
    print("You can now transfer this folder to Toolforge to streamline initialization.")
