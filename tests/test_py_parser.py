import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocessing.extract_structural_entities import extract_code_entities

def test_py_parser():
    print("Running Python Parser Tests...")
    example_py = Path(__file__).parent / "example.py"
    with open(example_py, "rb") as f:
        code_bytes = f.read().replace(b"\r\n", b"\n")
    
    entities = extract_code_entities(code_bytes, ".py")
    
    # 1. Test Uniqueness
    names = [e["name"] for e in entities]
    assert len(names) == len(set(names)), f"Duplicates found in Python: {names}"
    
    # 2. Test Key Entities Presence
    found_names = set(names)
    expected = [
        "Colour",
        "Outer",
        "Outer::Status",
        "Outer::InnerStruct",
        "Outer::InnerStruct::__init__(self, name: str, code: int)",
        "Outer::get_multiplier(self, factor: int)",
        "Outer::get_multiplier::multiplier(x: int)",
        "Point",
        "Box",
        "function_with_local_class()",
        "function_with_local_class::LocalClass",
        "function_with_local_class::LocalClass::add(a: int, b: int)"
    ]
    
    for exp in expected:
        assert any(exp in f for f in found_names), f"Missing Python entity: {exp}"

    print("Python Parser Tests Passed!")

if __name__ == "__main__":
    test_py_parser()
