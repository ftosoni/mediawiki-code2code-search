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
def mock_faiss_index():
    """Create a mock FAISS index"""
    index = MagicMock()
    index.ntotal = 2
    # Mock search to return indices [0, 1] and some dummy distances
    index.search.return_value = (np.array([[0.1, 0.5]], dtype='float32'), np.array([[0, 1]], dtype='int64'))
    return index

@pytest.fixture
def client(mock_db, mock_faiss_index):
    """FastAPI test client with mocked models and database"""
    # Mock the models before importing app
    with patch("app.SentenceTransformer") as mock_st, \
         patch("faiss.read_index") as mock_read_index, \
         patch("app.METADATA_DB_PATH", mock_db), \
         patch("app.FAISS_INDEX_PATH", "fake_index_path"):
        
        # Configure mock SentenceTransformer
        mock_model = MagicMock()
        # Mock encode to return a 512-dim vector
        mock_model.encode.return_value = np.zeros((1, 512), dtype='float32')
        mock_st.return_value = mock_model
        
        # Configure mock faiss.read_index
        mock_read_index.return_value = mock_faiss_index
        
        from app import app
        with TestClient(app) as c:
            yield c
