import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocessing.extract_structural_entities import extract_code_entities

def test_ts_parser():
    print("Running TypeScript Parser Tests...")
    example_ts = Path("tests/example.ts")
    with open(example_ts, "rb") as f:
        code_bytes = f.read().replace(b"\r\n", b"\n")
    
    entities = extract_code_entities(code_bytes, ".ts")
    
    # 1. Test Uniqueness
    names = [e["name"] for e in entities]
    assert len(names) == len(set(names)), f"Duplicates found in TS: {names}"
    
    # 2. Test Key Entities Presence
    found_names = set(names)
    expected = [
        "Text",
        "IntVector",
        "Colour",
        "StatusEnum",
        "Outer::Status",
        "Outer::InnerStruct",
        "Outer::InnerStruct::constructor",
        "Outer::InnerInterface",
        "OuterClass",
        "OuterClass::constructor",
        "OuterClass::getMultiplier",
        "OuterClass::getMultiplier::innerHelper",
        "Box",
        "Point",
        "functionWithLocalClass",
        "functionWithLocalClass::LocalClass",
        "functionWithLocalClass::LocalInterface",
        "functionWithLocalClass::LocalAlias"
    ]
    
    for exp in expected:
        assert any(exp in f for f in found_names), f"Missing TS entity: {exp}"

    print("TypeScript Parser Tests Passed!")

if __name__ == "__main__":
    test_ts_parser()
