import sqlite3
import os

WORKSPACE = r"c:\Users\franc\Documents\GitHub\mediawiki-code2code-search"
DB_PATH = os.path.join(WORKSPACE, "backend", "functions.db")

def delete_repo():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    repo_name = 'easypage-ai-deletion_scheduled-3364'
    
    print(f"Counting rows for {repo_name}...")
    cursor.execute("SELECT COUNT(*) FROM functions WHERE repo_name = ?", (repo_name,))
    count_before = cursor.fetchone()[0]
    print(f"Rows before: {count_before}")
    
    if count_before == 0:
        print("No rows found to delete.")
        conn.close()
        return

    print(f"Deleting rows...")
    cursor.execute("DELETE FROM functions WHERE repo_name = ?", (repo_name,))
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM functions WHERE repo_name = ?", (repo_name,))
    count_after = cursor.fetchone()[0]
    print(f"Rows after: {count_after}")
    
    # Optional: vacuum to reclaim space, but 1.3GB might take a while.
    # print("Vacuuming database...")
    # conn.execute("VACUUM")
    
    conn.close()
    print("✅ Deletion from functions.db complete.")

if __name__ == "__main__":
    delete_repo()
