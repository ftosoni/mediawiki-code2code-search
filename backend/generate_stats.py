import sqlite3
import os
import re
from collections import Counter

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "functions.db")

def categorize_type(entity_type, code):
    """Categorize entity into English labels based on native DB types."""
    mapping = {
        'function': "Functions",
        'type': "Types",
        'template': "Templates"
    }
    return mapping.get(entity_type, "Others")

def get_file_extension(filepath):
    """Extract file extension from path."""
    _, ext = os.path.splitext(filepath)
    return ext or "no extension"

def generate_stats():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Fetching data from database...")
    cursor.execute("SELECT repo_group, filepath, type, code FROM functions")
    rows = cursor.fetchall()

    repo_group_stats = Counter()
    extension_stats = Counter()
    category_stats = Counter()

    for repo_group, filepath, entity_type, code in rows:
        # Category
        category = categorize_type(entity_type, code)
        category_stats[category] += 1

        # Repo Group
        repo_group_stats[repo_group] += 1

        # File Extension
        ext = get_file_extension(filepath)
        extension_stats[ext] += 1

    conn.close()

    # Output Results
    print("\n" + "="*40)
    print(" MEDIAWIKI CODE ENTITY STATISTICS")
    print("="*40)

    print("\n--- Statistics by Category ---")
    for cat, count in category_stats.most_common():
        print(f"{cat:<20}: {count:>8}")

    print("\n--- Statistics by Repository Group ---")
    for group, count in repo_group_stats.most_common():
        print(f"{group:<20}: {count:>8}")

    print("\n--- Statistics by File Extension ---")
    for ext, count in extension_stats.most_common():
        print(f"{ext:<20}: {count:>8}")

    print("\n" + "="*40)
    print(f" Total Entities: {len(rows):>18}")
    print("="*40)

if __name__ == "__main__":
    generate_stats()
