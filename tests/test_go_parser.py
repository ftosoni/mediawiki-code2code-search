import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocessing.extract_structural_entities import extract_code_entities

def test_go_parser():
    print("Running Go Parser Tests...")
    example_go = Path(__file__).parent / "example.go"
    with open(example_go, "rb") as f:
        code_bytes = f.read().replace(b"\r\n", b"\n")
    
    entities = extract_code_entities(code_bytes, ".go")
    
    # 1. Test Uniqueness
    names = [e["name"] for e in entities]
    assert len(names) == len(set(names)), f"Duplicates found in Go: {names}"
    
    # 2. Test Key Entities Presence
    found_names = set(names)
    expected = [
        "Text",
        "IntVector",
        "Colour",
        "Outer",
        "Shape",
        "ShapeType",
        "Box",
        "Wrapper",
        "functionWithLocalClass",
        "functionWithLocalClass::LocalStruct",
        "GetMultiplierMethod(factor int)"
    ]
    
    for exp in expected:
        assert any(exp in f for f in found_names), f"Missing Go entity: {exp}"

    print("Go Parser Tests Passed!")

if __name__ == "__main__":
    test_go_parser()
