import torch
import os
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import time

def test_quantization():
    model_id = "jinaai/jina-reranker-v2-base-multilingual"
    # To save time in the test, we'll try to load it from the local cache if available
    local_path = os.path.join("models", "jina-reranker")
    path = local_path if os.path.exists(local_path) else model_id
    
    print(f"Loading model from {path}...")
    model = AutoModelForSequenceClassification.from_pretrained(
        path, 
        trust_remote_code=True,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=False
    ).to("cpu")
    model.eval()
    
    tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
    
    query = "how to parse json"
    doc = "To parse JSON in PHP, use json_decode($json_string)."
    
    # Original Inference
    start = time.time()
    with torch.no_grad():
        if hasattr(model, 'compute_score'):
            scores_orig = model.compute_score([[query, doc]])
            score_orig = scores_orig[0] if isinstance(scores_orig, (list, np.ndarray)) else scores_orig
        else:
            inputs = tokenizer([query, doc], return_tensors="pt", padding=True, truncation=True)
            score_orig = model(**inputs).logits[0].item()
    orig_time = time.time() - start
    print(f"Original Score: {score_orig:.4f}, Time: {orig_time:.4f}s")
    
    # Quantized Inference
    print("\nApplying dynamic quantization (int8)...")
    quantized_model = torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8
    )
    
    start = time.time()
    with torch.no_grad():
        if hasattr(quantized_model, 'compute_score'):
            scores_quant = quantized_model.compute_score([[query, doc]])
            score_quant = scores_quant[0] if isinstance(scores_quant, (list, np.ndarray)) else scores_quant
        else:
            inputs = tokenizer([query, doc], return_tensors="pt", padding=True, truncation=True)
            score_quant = quantized_model(**inputs).logits[0].item()

    quant_time = time.time() - start
    print(f"Quantized Score: {score_quant:.4f}, Time: {quant_time:.4f}s")
    
    speedup = orig_time / quant_time
    print(f"\nSpeedup: {speedup:.2f}x")
    print(f"Score difference: {abs(score_orig - score_quant):.6f}")

if __name__ == "__main__":
    test_quantization()
