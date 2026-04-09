import sys
import os
import asyncio
from pydantic import BaseModel
import time

# Mock requirements
class SearchRequest(BaseModel):
    query: str
    repo_group: str = "all"
    type_filter: str = "all"
    top_k: int = 10

async def test_search():
    # Import app and its globals
    from app import app, bi_model, index, rerank_model, search_code
    
    print("Models loaded (from app.py session)...")
    req = SearchRequest(query="how to parse json in php")
    
    print("\n--- Starting Search Test ---")
    results = await search_code(req)
    print("--- Search Test Done ---\n")

if __name__ == "__main__":
    # We need to make sure models are initialized. 
    # Since app.py initializes them at module level, this might take time.
    asyncio.run(test_search())
