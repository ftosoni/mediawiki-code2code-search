import sys
import os
from pathlib import Path
import pytest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocessing.extract_structural_entities import extract_code_entities

def get_example_cpp_entities():
    example_path = Path(__file__).parent / "example.cpp"
    with open(example_path, "rb") as f:
        code_bytes = f.read().replace(b"\r\n", b"\n")
    return extract_code_entities(code_bytes, ".cpp")

@pytest.fixture
def example_cpp_entities():
    return get_example_cpp_entities()

def test_entity_uniqueness(example_cpp_entities):
    """Ensure each entity is extracted once and only once (by name and scope)."""
    names = [(e["name"], e["type"]) for e in example_cpp_entities]
    unique_names = set(names)
    assert len(names) == len(unique_names), f"Duplicates found: {[n for n in unique_names if names.count(n) > 1]}"

def test_expected_types_exist(example_cpp_entities):
    """Verify that all core types (classes, structs, enums) are extracted."""
    # Capture 'template' as well since templated types use that capture name
    found_names = {e["name"] for e in example_cpp_entities if e["type"] in ["type", "template"]}
    expected_types = {
        "Colour", "Outer", "Outer::Status", "Point", "Shape", "Shape::Type", 
        "Box", "Container", "Container::Operation", "Wrapper", "Wrapper::InnerStruct",
        "Wrapper::demonstrateLocalClass::LocalClass", "functionWithLocalClass::Local", 
        "functionWithLocalClass::Local::LocalEnum", "functionWithLocalClass::Local::LocalStruct"
    }
    missing = expected_types - found_names
    assert not missing, f"Missing types: {missing}"

def test_expected_functions_exist(example_cpp_entities):
    """Verify that all expected functions are extracted."""
    # Group functions and templates (since template functions use 'template' capture)
    found_names = {e["name"] for e in example_cpp_entities if e["type"] in ["function", "template"]}
    # Note: Constructors often have the same name as the class. 
    # In C++, we want them if they are separate definitions.
    # Some might be qualified (e.g. Wrapper::Wrapper) or simple (add).
    
    # We check for existence of base names or qualified names
    expected_functions = {
        "maxValue", "printColour", "functionWithLocalClass",
        "getMultiplier", "demonstrateLocalClass", "add", 
        "Container::transform", "Wrapper::transform"
    }
    
    # Check if these base names exist in any of the found function names
    for exp in expected_functions:
        assert any(exp in f for f in found_names), f"Missing function: {exp}"

def test_no_aliases_extracted(example_cpp_entities):
    """Ensure simple type aliases (using/typedef) are NOT extracted unless they are template declarations."""
    # Aliases like 'Text', 'IntVector', 'uint' should be excluded.
    # Note: 'Vec' is a template alias, so it IS extracted as a template.
    forbidden = {"Text", "IntVector", "uint", "PreferredColour", "LocalAlias", "LocalTypedef"}
    found_names = {e["name"] for e in example_cpp_entities}
    intersection = forbidden & found_names
    assert not intersection, f"Filtered aliases should not be present: {intersection}"

def test_prioritize_definition_over_declaration(example_cpp_entities):
    """Ensure that for maxValue, we got the definition (with body), not just the declaration."""
    max_value_ent = [e for e in example_cpp_entities if "maxValue" in e["name"]][0]
    # Definition of maxValue in example.cpp is about 5 lines. Declaration is 2.
    # Definition of maxValue in example.cpp is about 5 lines.
    assert max_value_ent["end_line"] - max_value_ent["start_line"] >= 3, "Should have captured the definition of maxValue"

if __name__ == "__main__":
    # Minimal runner to avoid pytest dependency issues in venv
    print("Running C++ Parser Tests...")
    try:
        example = get_example_cpp_entities()
        test_entity_uniqueness(example)
        test_expected_types_exist(example)
        test_expected_functions_exist(example)
        test_no_aliases_extracted(example)
        test_prioritize_definition_over_declaration(example)
        print("ALL TESTS PASSED!")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
