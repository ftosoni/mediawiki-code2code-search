import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocessing.extract_structural_entities import extract_code_entities

def test_java_parser():
    print("Running Java Parser Tests...")
    example_java = Path(__file__).parent / "example.java"
    with open(example_java, "rb") as f:
        code_bytes = f.read().replace(b"\r\n", b"\n")
    
    entities = extract_code_entities(code_bytes, ".java")
    
    # 1. Test Uniqueness
    names = [e["name"] for e in entities]
    assert len(names) == len(set(names)), f"Duplicates found in Java: {names}"
    
    # 2. Test Key Entities Presence
    found_names = set(names)
    expected = [
        "Text",
        "IntVector",
        "Colour",
        "Outer",
        "Outer::Status",
        "Outer::InnerStruct",
        "Outer::getMultiplier(int factor)",
        "Box",
        "Point",
        "Main",
        "Main::functionWithLocalClass()",
        "Main::functionWithLocalClass::LocalClass",
        "Main::functionWithLocalClass::LocalClass::add(int a, int b)"
    ]
    
    for exp in expected:
        assert any(exp in f for f in found_names), f"Missing Java entity: {exp}"

    print("Java Parser Tests Passed!")

if __name__ == "__main__":
    test_java_parser()
