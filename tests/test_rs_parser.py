import unittest
import os
from preprocessing.extract_structural_entities import extract_code_entities

class TestRustParser(unittest.TestCase):
    def test_rs_extraction(self):
        with open("tests/example.rs", "rb") as f:
            code = f.read()
        entities = extract_code_entities(code, ".rs")
        
        names = [e["name"] for e in entities]
        
        expected = [
            "Text", "IntVector", "Colour", "Outer", "InnerStruct", 
            "Shape", "ShapeType", "Box", "Wrapper", 
            "function_with_local_class", "function_with_local_class::LocalStruct",
            "function_with_local_class::nested_function",
            "wrapper_get_multiplier"
        ]
        
        for name in expected:
            self.assertTrue(any(name in n for n in names), f"Missing {name} in {names}")
            
    def test_rs_scoping(self):
        with open("tests/example.rs", "rb") as f:
            code = f.read()
        entities = extract_code_entities(code, ".rs")
        names = [e["name"] for e in entities]
        
        # Verify specific qualified names
        self.assertIn("function_with_local_class::LocalStruct", names)
        self.assertIn("function_with_local_class::nested_function", names)
        # closure helpers usually don't get qualified names unless we capture them specially
        # but nested_function::inner_helper should
        self.assertIn("function_with_local_class::nested_function::inner_helper", names)

if __name__ == "__main__":
    unittest.main()
