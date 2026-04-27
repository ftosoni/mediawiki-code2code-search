# This file is part of MediaWiki Code2Code Search
# <https://github.com/ftosoni/mediawiki-code2code-search>.
# Copyright (c) 2026 Francesco Tosoni.

import pytest
from unittest.mock import patch

def test_health(client):
    """Test the /health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "index_size" in data

def test_search(client):
    """Test the /search endpoint"""
    search_payload = {
        "query": "hello world",
        "top_k": 5,
        "repo_group": "all",
        "type_filter": "all",
        "language_filter": "all"
    }
    response = client.post("/search", json=search_payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    # Check if we got our dummy data back
    assert data["results"][0]["name"] == "hello"

def test_search_with_filters(client):
    """Test /search with specific filters"""
    # Test language filter
    search_payload = {
        "query": "find javascript",
        "top_k": 5,
        "repo_group": "all",
        "type_filter": "all",
        "language_filter": ["JavaScript"]
    }
    response = client.post("/search", json=search_payload)
    assert response.status_code == 200
    results = response.json()["results"]
    for res in results:
        assert res["filepath"].endswith(".js")

def test_get_code_snippet(client):
    """Test the /code endpoint"""
    swhid = "swh:1:cnt:abc123lines=1-10"
    
    response = client.get(f"/code?swhid={swhid}")
    assert response.status_code == 200
    data = response.json()
    assert "code" in data
    assert "def hello()" in data["code"]

def test_invalid_swhid(client):
    """Test /code with invalid SWHID"""
    response = client.get("/code?swhid=invalid_id")
    assert response.status_code == 400
    assert "detail" in response.json()
