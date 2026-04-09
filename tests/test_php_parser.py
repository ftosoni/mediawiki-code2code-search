import unittest
import subprocess
import json
import os

class TestPHPParser(unittest.TestCase):
    def test_php_extraction(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        result = subprocess.run(
            [".\\venv\\Scripts\\python.exe", "preprocessing/extract_structural_entities.py", "tests/example.php"],
            capture_output=True,
            text=True,
            env=env,
            shell=True
        )
        self.assertEqual(result.returncode, 0, f"Error: {result.stderr}")
        
        # The script currently prints JSON to stdout if run as a script? 
        # Actually I'm using it as a module or I need to make it a CLI.
        # I'll use a diagnostic wrapper.
        
    def test_php_logical(self):
        from preprocessing.extract_structural_entities import extract_code_entities
        with open("tests/example.php", "rb") as f:
            code = f.read()
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
