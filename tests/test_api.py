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

def test_locales(client):
    """Test the /locales endpoint discovers locales from frontend/i18n"""
    response = client.get("/locales")
    assert response.status_code == 200
    data = response.json()
    codes = [locale["code"] for locale in data["locales"]]
    assert data["default"] == "en"
    assert "en" in codes
    # qqq.json is message documentation for translatewiki, not a selectable locale.
    assert "qqq" not in codes
    assert codes == sorted(codes)

def test_locale_autonyms(client):
    """Autonyms must come from CLDR, not be the bare code echoed back"""
    autonyms = {loc["code"]: loc["autonym"] for loc in client.get("/locales").json()["locales"]}
    assert autonyms["en"] == "English"
    # Locales Chromium's reduced Intl dataset gets wrong; this is why we resolve server-side.
    assert autonyms.get("as") == "অসমীয়া"
    assert autonyms.get("sat") == "ᱥᱟᱱᱛᱟᱲᱤ"

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
