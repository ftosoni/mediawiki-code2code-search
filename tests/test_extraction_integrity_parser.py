import sys
import os
from pathlib import Path
import pytest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocessing.extract_structural_entities import extract_code_entities

@pytest.mark.parametrize("ext", [
    ".py", ".cpp", ".c", ".php", ".js", ".ts", ".lua", ".go", ".java", ".rs"
])
def test_extraction_line_integrity(ext):
    """
    Critical integrity test: Verify that the 'code' content extracted for 
    each entity actually matches the number of lines between start_line and end_line.
    This prevents 'bloat' bugs where leaked variables cause trailing code to be included.
    """
    # Find the corresponding example file for this extension
    example_file = Path(__file__).parent / f"example{ext}"
    if not example_file.exists():
        pytest.skip(f"Example file for {ext} not found")
        
    with open(example_file, "rb") as f:
        code_bytes = f.read().replace(b"\r\n", b"\n")
    
    entities = extract_code_entities(code_bytes, ext)
    
    assert len(entities) > 0, f"No entities extracted for {ext}"
    
    for ent in entities:
        name = ent["name"]
        start = ent["start_line"]
        end = ent["end_line"]
        code = ent["code"]
        
        # Invariant: extracted code lines must equal line range
        # Note: we use splitlines() which handles trailing newlines fairly
        # Some languages might have comments included, which is fine, 
        # but the line count must be consistent.
        lines = code.splitlines()
        expected_count = end - start + 1
        
        # We allow a +/- 1 difference in some edge cases if necessary, 
        # but the bloat bug caused massive differences (e.g. 5 vs 500).
        diff = abs(len(lines) - expected_count)
        
        assert diff <= 1, (
            f"Line count mismatch for {name} ({ext}): "
            f"Range {start}-{end} ({expected_count} lines) "
            f"but extracted code has {len(lines)} lines.\n"
            f"Potential bloat or slicing bug detected!"
        )

if __name__ == "__main__":
    # Allow running directly
    for ext in [".py", ".cpp", ".c", ".php", ".js", ".ts", ".lua", ".go", ".java", ".rs"]:
        try:
            test_extraction_line_integrity(ext)
            print(f"PASS: {ext}")
        except Exception as e:
            print(f"FAIL: {ext} - {e}")
