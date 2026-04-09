import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocessing.extract_structural_entities import extract_code_entities

def test_c_parser():
    print("Running C Parser Tests...")
    example_c = Path("tests/example.c")
    with open(example_c, "rb") as f:
        code_bytes = f.read().replace(b"\r\n", b"\n")
    
    entities = extract_code_entities(code_bytes, ".c")
    
    # 1. Test Uniqueness
    names = [e["name"] for e in entities]
    assert len(names) == len(set(names)), f"Duplicates found in C: {names}"
    
    # 2. Test Key Entities Presence
    found_names = set(names)
    expected = [
        "IntVector",
        "Colour",
        "Outer",
        "Outer::Status",
        "Outer::InnerStruct",
        "Shape",
        "Shape::Type",
        "Wrapper",
        "function_with_local_struct(void)",
        "function_with_local_struct::LocalStruct",
        "Point"
    ]
    
    for exp in expected:
        assert any(exp in f for f in found_names), f"Missing C entity: {exp}"

    print("C Parser Tests Passed!")

if __name__ == "__main__":
    test_c_parser()
