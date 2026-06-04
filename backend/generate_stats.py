import sqlite3
import os
import json
from collections import Counter, defaultdict
from urllib.parse import urlparse

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "snippets.db")
INDEX_PATH = os.path.join(BASE_DIR, "mediawiki.index")
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "embeddings.npy")
REPOS_LIST_PATH = os.path.join(BASE_DIR, "..", "preprocessing", "repos_list.json")
FAILED_CLONES_PATH = os.path.join(BASE_DIR, "..", "preprocessing", "failed_clones.json")

EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".cpp": "C++",
    ".hpp": "C++",
    ".h": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".php": "PHP",
    ".inc": "PHP",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".lua": "Lua",
    ".go": "Go",
    ".java": "Java",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".pl": "Perl",
    ".pm": "Perl"
}

def get_file_size_string(path):
    """Return human-readable size of file."""
    if not os.path.exists(path):
        return "Not found"
    size_bytes = os.path.getsize(path)
    if size_bytes >= 1024**3:
        return f"{size_bytes / (1024**3):.2f} GB"
    elif size_bytes >= 1024**2:
        return f"{size_bytes / (1024**2):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes} bytes"

def get_file_extension(filepath):
    """Extract file extension from path."""
    _, ext = os.path.splitext(filepath)
    return ext.lower()

def get_forge(url):
    """Extract source forge domain from repository URL."""
    try:
        netloc = urlparse(url).netloc
        if not netloc:
            if "@" in url:
                netloc = url.split("@")[-1].split(":")[0]
            else:
                netloc = url.split("/")[2]
        return netloc
    except Exception:
        return "unknown"

def generate_stats():
    # 1. File Size Statistics
    print("\n" + "="*50)
    print(" MEDIAWIKI SEARCH COMPONENT SIZES")
    print("="*50)
    print(f"{'Plain Embeddings (embeddings.npy)':<35}: {get_file_size_string(EMBEDDINGS_PATH):>12}")
    print(f"{'Metadata Database (snippets.db)':<35}: {get_file_size_string(DB_PATH):>12}")
    print(f"{'FAISS Search Index (mediawiki.index)':<35}: {get_file_size_string(INDEX_PATH):>12}")
    print("="*50)

    if not os.path.exists(DB_PATH):
        print(f"\nError: {DB_PATH} not found. Cannot calculate detailed statistics.")
        return

    # 2. Database query for counts
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\nAnalyzing database entries...")
    rows = []
    db_repos = set()
    try:
        cursor.execute("SELECT repo_group, filepath, type FROM snippets")
        rows = cursor.fetchall()
        
        cursor.execute("SELECT DISTINCT repo_group, repo_name FROM snippets")
        db_repos = set(cursor.fetchall())
    except Exception as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()

    total_entities = len(rows)
    if total_entities == 0:
        print("No entries found in database.")
        return

    repo_group_stats = Counter()
    lang_stats = Counter()
    category_stats = Counter()
    lang_type_stats = defaultdict(lambda: Counter()) # language -> {type -> count}

    for repo_group, filepath, entity_type in rows:
        # Category
        mapping = {'function': 'Functions', 'type': 'Types', 'template': 'Templates'}
        category = mapping.get(entity_type, 'Others')
        category_stats[category] += 1

        # Repo Group
        repo_group_stats[repo_group] += 1

        # Language mapping
        ext = get_file_extension(filepath)
        lang = EXTENSION_TO_LANGUAGE.get(ext, f"Unknown ({ext})" if ext else "No extension")
        lang_stats[lang] += 1
        lang_type_stats[lang][category] += 1

    # Load metadata lists for source forge statistics
    repos_list = []
    failed_clones = []
    
    if os.path.exists(REPOS_LIST_PATH):
        try:
            with open(REPOS_LIST_PATH, "r", encoding="utf-8") as f:
                repos_list = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read {REPOS_LIST_PATH}: {e}")
            
    if os.path.exists(FAILED_CLONES_PATH):
        try:
            with open(FAILED_CLONES_PATH, "r", encoding="utf-8") as f:
                failed_clones = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read {FAILED_CLONES_PATH}: {e}")

    # Process repositories by forge
    repo_to_url = {}
    total_by_forge = Counter()
    for item in repos_list:
        url = item.get("url", "")
        group = item.get("group", "")
        name = url.split('/')[-1].replace('.git', '')
        repo_to_url[(name, group)] = url
        forge = get_forge(url)
        total_by_forge[forge] += 1
        
    indexed_by_forge = Counter()
    for group, name in db_repos:
        url = repo_to_url.get((name, group))
        if url:
            forge = get_forge(url)
        else:
            forge = "unknown"
        indexed_by_forge[forge] += 1
        
    failed_by_forge = Counter()
    for item in failed_clones:
        url = item.get("url", "")
        forge = get_forge(url)
        failed_by_forge[forge] += 1

    # Output Results
    print("\n" + "="*50)
    print(" MEDIAWIKI CODE ENTITY STATISTICS")
    print("="*50)

    print("\n--- Statistics by Category ---")
    for cat, count in category_stats.most_common():
        percentage = (count / total_entities) * 100
        print(f"{cat:<20}: {count:>8} ({percentage:.1f}%)")

    print("\n--- Statistics by Programming Language ---")
    # Sort languages by overall frequency
    sorted_langs = sorted(lang_stats.items(), key=lambda x: x[1], reverse=True)
    for lang, total_count in sorted_langs:
        percentage = (total_count / total_entities) * 100
        print(f"{lang:<20}: {total_count:>8} ({percentage:.1f}%)")
        # Detail types
        details = []
        for cat in ["Functions", "Types", "Templates", "Others"]:
            cnt = lang_type_stats[lang][cat]
            if cnt > 0:
                details.append(f"{cat}: {cnt}")
        if details:
            print(f"  +- {', '.join(details)}")

    print("\n--- Statistics by Repository Group ---")
    for group, count in repo_group_stats.most_common():
        percentage = (count / total_entities) * 100
        print(f"{group:<20}: {count:>8} ({percentage:.1f}%)")

    print("\n--- Statistics by Source Forge ---")
    all_forges = sorted(list(set(total_by_forge.keys()) | set(indexed_by_forge.keys()) | set(failed_by_forge.keys())))
    sum_total = 0
    sum_indexed = 0
    sum_failed = 0
    for forge in all_forges:
        total = total_by_forge[forge]
        indexed = indexed_by_forge[forge]
        failed = failed_by_forge[forge]
        print(f"{forge:<30}: {indexed:>5} indexed, {failed:>5} failed (total listed: {total})")
        sum_total += total
        sum_indexed += indexed
        sum_failed += failed
    print(f"{'Total':<30}: {sum_indexed:>5} indexed, {sum_failed:>5} failed (total listed: {sum_total})")

    print("\n" + "="*50)
    print(f" Total Code Snippets: {total_entities:>26}")
    print("="*50)

if __name__ == "__main__":
    generate_stats()
