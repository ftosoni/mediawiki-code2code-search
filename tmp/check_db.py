import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Check both relative to script and absolute if script is in /tmp
# In this environment, I'll use the absolute path relative to workspace
WORKSPACE = r"c:\Users\franc\Documents\GitHub\mediawiki-code2code-search"
DB_PATH = os.path.join(WORKSPACE, "backend", "functions.db")

def check():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Try different search criteria
    repo_pattern = "%easypage-ai-deletion_scheduled-3364%"
    
    print(f"Searching for {repo_pattern}...")
    cursor.execute("SELECT repo_name, repo_group, COUNT(*) FROM functions WHERE repo_name LIKE ? OR repo_group LIKE ? GROUP BY repo_name, repo_group", (repo_pattern, repo_pattern))
    results = cursor.fetchall()
    
    if not results:
        print("No matches found.")
    else:
        for row in results:
            print(f"Match: repo_name='{row[0]}', repo_group='{row[1]}', count={row[2]}")
            
    conn.close()

if __name__ == "__main__":
    check()
