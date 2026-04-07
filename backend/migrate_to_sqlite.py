# This file is part of MediaWiki Code2Code Search
# <https://github.com/ftosoni/mediawiki-code2code-search>.
# Copyright (c) 2026 Francesco Tosoni.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import sqlite3
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Use raw_functions.json which contains the code snippets
JSON_PATH = os.path.join(BASE_DIR, "raw_functions.json")
DB_PATH = os.path.join(BASE_DIR, "functions.db")

def migrate():
    if not os.path.exists(JSON_PATH):
        print(f"Error: {JSON_PATH} not found.")
        return

    print(f"Reading {JSON_PATH} (this may take a moment)...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Creating database at {DB_PATH}...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # We use an integer id that matches the position in the original list
    # so we can directly map FAISS results to rows.
    cursor.execute('''
        CREATE TABLE functions (
            id INTEGER PRIMARY KEY,
            original_id TEXT,
            swhid TEXT,
            sha1 TEXT,
            repo_name TEXT,
            repo_group TEXT,
            filepath TEXT,
            name TEXT,
            type TEXT,
            code TEXT
        )
    ''')

    print(f"Inserting {len(data)} entries...")
    
    # Prepare data for insertion
    entries = []
    for i, item in enumerate(data):
        entries.append((
            i, 
            item.get("id"), 
            item.get("swhid"), 
            item.get("sha1"), 
            item.get("repo_name"), 
            item.get("repo_group"), 
            item.get("filepath"), 
            item.get("name"), 
            item.get("type"),
            item.get("code_for_embedding") # This is the crucial snippet
        ))

    cursor.executemany('''
        INSERT INTO functions (id, original_id, swhid, sha1, repo_name, repo_group, filepath, name, type, code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', entries)

    print("Creating indexes...")
    cursor.execute('CREATE INDEX idx_swhid ON functions(swhid)')
    cursor.execute('CREATE INDEX idx_sha1 ON functions(sha1)')
    
    conn.commit()
    conn.close()
    print("✅ Migration complete.")

if __name__ == "__main__":
    migrate()
