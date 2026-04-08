# This file is part of MediaWiki Code2Code Search
# <https://github.com/ftosoni/mediawiki-code2code-search>.
# Copyright (c) 2026 Francesco Tosoni.

import pytest
import sqlite3
import os
import faiss
import numpy as np
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

@pytest.fixture
def mock_db(tmp_path):
    """Create a temporary SQLite database for testing"""
    db_path = tmp_path / "test_functions.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the same schema as in production
    cursor.execute("""
        CREATE TABLE functions (
            id INTEGER PRIMARY KEY,
            swhid TEXT,
            sha1 TEXT,
            repo_name TEXT,
            repo_group TEXT,
            filepath TEXT,
            language TEXT,
            type TEXT,
            name TEXT,
            signature TEXT,
            code_content TEXT
        )
    """)
    
    # Add dummy data
    sample_data = [
        (0, "swh:1:cnt:abc123lines=1-10", "abc123sha1", "mediawiki/core", "core", "test.py", "Python", "function", "hello", "def hello()", "def hello():\n    print('world')"),
        (1, "swh:1:cnt:def456lines=1-5", "def456sha1", "mediawiki/extensions/VisualEditor", "extensions", "ve.js", "JavaScript", "function", "init", "function init()", "function init() {\n  return 1;\n}")
    ]
    cursor.executemany("INSERT INTO functions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_data)
    conn.commit()
    conn.close()
    return str(db_path)

@pytest.fixture
def test_faiss_index(tmp_path):
    """Create a small real FAISS index for testing"""
    index_path = tmp_path / "test_mediawiki.index"
    d = 512  # Jina dimension
    index = faiss.IndexFlatL2(d)
    # Add 2 dummy vectors corresponding to our dummy DB entries
    xb = np.zeros((2, d)).astype('float32')
    index.add(xb)
    faiss.write_index(index, str(index_path))
    return str(index_path)

@pytest.fixture
def client(mock_db, test_faiss_index):
    """FastAPI test client with mocked models and real test database/index"""
    # Mock the heavy models before importing app
    with patch("app.SentenceTransformer") as mock_st, \
         patch("app.METADATA_DB_PATH", mock_db), \
         patch("app.FAISS_INDEX_PATH", test_faiss_index):
        
        # Configure mock SentenceTransformer
        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((1, 512), dtype='float32')
        mock_st.return_value = mock_model
        
        # Now we can import the app which will trigger the lifespan
        # with the patched paths
        from app import app
        with TestClient(app) as c:
            yield c
