import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocessing.extract_structural_entities import extract_code_entities

def test_js_parser():
    print("Running JavaScript Parser Tests...")
    example_js = Path("tests/example.js")
    with open(example_js, "rb") as f:
        code_bytes = f.read().replace(b"\r\n", b"\n")
    
    entities = extract_code_entities(code_bytes, ".js")
    
    # 1. Test Uniqueness
    names = [e["name"] for e in entities]
    assert len(names) == len(set(names)), f"Duplicates found in JS: {names}"
    
    # 2. Test Key Entities Presence
    found_names = set(names)
    expected = [
        "Outer",
        "Outer::constructor",
        "Outer::getMultiplier",
        "Outer::getMultiplier::innerHelper",
        "functionWithLocalClass",
        "functionWithLocalClass::LocalClass",
        "functionWithLocalClass::LocalClass::add"
    ]
    
    for exp in expected:
        assert any(exp in f for f in found_names), f"Missing JS entity: {exp}"

    print("JavaScript Parser Tests Passed!")

if __name__ == "__main__":
    test_js_parser()
