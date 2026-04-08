# This file is part of MediaWiki Code2Code Search
# <https://github.com/ftosoni/mediawiki-code2code-search>.
# Copyright (c) 2026 Francesco Tosoni.

import httpx
import pytest

@pytest.mark.asyncio
async def test_huggingface_model_reachable():
    """Verify that the model repository on Hugging Face is reachable"""
    model_ids = [
        "jinaai/jina-code-embeddings-0.5b",
        "jinaai/jina-reranker-v2-base-multilingual"
    ]
    
    async with httpx.AsyncClient() as client:
        for model_id in model_ids:
            url = f"https://huggingface.co/{model_id}/resolve/main/config.json"
            # We use HEAD to check existence without downloading
            response = await client.head(url, follow_redirects=True)
            # 200 is expected, or 302/200 if redirected
            assert response.status_code == 200, f"Model {model_id} config not reachable at {url}"

@pytest.mark.asyncio
async def test_swh_s3_reachable():
    """Verify that SWH S3 endpoint is reachable"""
    url = "https://softwareheritage.s3.amazonaws.com/"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        # S3 root usually returns 200 or 403 (if forbidden but exists)
        # For our purposes, we just want to ensure it's not a 404 or connection error
        assert response.status_code in [200, 403]
