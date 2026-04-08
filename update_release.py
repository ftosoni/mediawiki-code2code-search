import re
import os
import sys
import argparse
from datetime import datetime

def update_release(swhid, commit):
    # Clean up SWHID (remove newlines and extra spaces)
    swhid = "".join(swhid.split()).strip()
    
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"Updating metadata with Date: {today}, SWHID: {swhid}, Commit: {commit}")

    # 1. CITATION.cff
    citation_path = "CITATION.cff"
    if os.path.exists(citation_path):
        print(f"Updating {citation_path}...")
        with open(citation_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Update SWHID value under swh identifier
        # Match type: swh followed by newline and indented value
        content = re.sub(r"(type: swh\s+value: ')[^']+", fr"\g<1>{swhid}", content)
        # Update commit
        content = re.sub(r"(commit: )[a-f0-9]+", fr"\g<1>{commit}", content)
        # Update date-released
        content = re.sub(r"(date-released: ')[^']+", fr"\g<1>{today}", content)
        
        with open(citation_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 2. codemeta.json
    codemeta_path = "codemeta.json"
    if os.path.exists(codemeta_path):
        print(f"Updating {codemeta_path}...")
        with open(codemeta_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Update datePublished
        content = re.sub(r'("datePublished": ")[^"]+', fr'\g<1>{today}', content)
        # Update identifier
        content = re.sub(r'("identifier": ")[^"]+', fr'\g<1>{swhid}', content)
        
        with open(codemeta_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 3. README.md
    readme_path = "README.md"
    if os.path.exists(readme_path):
        print(f"Updating {readme_path}...")
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract only the directory hash part for the README badge
        # SWHID format: swh:1:dir:<HASH>[;metadata...]
        hash_match = re.search(r"swh:1:dir:([a-f0-9]+)", swhid)
        if not hash_match:
            print(f"Warning: Could not extract hash from SWHID: {swhid}")
            return
        dir_hash = hash_match.group(1)

        # Update badge SWHID - match from dir: until the final badge URL slash
        content = re.sub(r"(archive\.softwareheritage\.org/badge/swh:1:dir:).*?(/)", fr"\g<1>{dir_hash}\g<2>", content)
        # Update link SWHID - replaces the WHOLE SWHID part in the archive link
        # The link looks like: .../swh:1:dir:OLD_SWHID)
        # We match until the closing parenthesis of the markdown link
        content = re.sub(r"(archive\.softwareheritage\.org/swh:1:dir:).*?(\))", fr"\g<1>{swhid.replace('swh:1:dir:', '')}\g<2>", content)
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)

    # 4. frontend/index.html
    html_path = os.path.join("frontend", "index.html")
    if os.path.exists(html_path):
        print(f"Updating {html_path}...")
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Update date in footer - targeting the specific pattern <span>YYYY-MM-DD</span>
        # We look for the one that already has a date-like string
        content = re.sub(r"<span>\d{4}-\d{2}-\d{2}</span>", f"<span>{today}</span>", content)
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)

    print("✅ All files updated successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update release metadata (SWHID, Commit, Date) in project files.")
    parser.add_argument("swhid", help="The Software Heritage Identifier (SWHID)")
    parser.add_argument("commit", help="The Git commit hash")
    
    args = parser.parse_args()
    update_release(args.swhid, args.commit)
