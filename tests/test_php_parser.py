import unittest
import subprocess
import json
import os
from pathlib import Path

class TestPHPParser(unittest.TestCase):
    def test_php_logical(self):
        from preprocessing.extract_structural_entities import extract_code_entities
        example_path = Path(__file__).parent / "example.php"
        with open(example_path, "rb") as f:
            code = f.read().replace(b"\r\n", b"\n")
        entities = extract_code_entities(code, ".php")
        
        names = [e["name"] for e in entities]
        
        expected = ["Text", "IntVector", "Colour", "Outer", "InnerStruct", "Box", "functionWithLocalClass", "LocalClass"]
        for name in expected:
            self.assertTrue(any(name in n for n in names), f"Missing {name} in {names}")
            
        # Check qualification if available
        # self.assertIn("Outer::InnerStruct", names)
        # self.assertIn("Outer::getMultiplier", names)

if __name__ == "__main__":
    unittest.main()
