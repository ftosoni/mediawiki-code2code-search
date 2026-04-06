import os
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer

base_path = "/data/project/code2codesearch/models"

print("Downloading Jina Embeddings...")
bi_model = SentenceTransformer("jinaai/jina-code-embeddings-0.5b", trust_remote_code=True)
bi_model.save(os.path.join(base_path, "jina-embeddings"))

print("Downloading Jina Reranker v3...")
model_name = "jinaai/jina-reranker-v3"
rerank_model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
rerank_tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

rerank_model.save_pretrained(os.path.join(base_path, "jina-reranker"))
rerank_tokenizer.save_pretrained(os.path.join(base_path, "jina-reranker"))

print("All saved in /data/project/code2codesearch/models")
