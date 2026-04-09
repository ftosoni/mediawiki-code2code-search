import sqlite3
import os

WORKSPACE = r"c:\Users\franc\Documents\GitHub\mediawiki-code2code-search"
DB_PATH = os.path.join(WORKSPACE, "backend", "functions.db")

def find_missing_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM functions ORDER BY id")
    existing_ids = set(row[0] for row in cursor.fetchall())
    conn.close()
    
    total_original = 907988
    all_possible = set(range(total_original))
    missing_ids = all_possible - existing_ids
    
    print(f"Found {len(missing_ids)} missing IDs.")
    return sorted(list(missing_ids))

if __name__ == "__main__":
    missing = find_missing_ids()
    # Save to a temp file for the next script
    with open("tmp/missing_ids.txt", "w") as f:
        for mid in missing:
            f.write(f"{mid}\n")
    print("Missing IDs saved to tmp/missing_ids.txt")
