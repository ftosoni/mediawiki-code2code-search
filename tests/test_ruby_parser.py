import unittest
from pathlib import Path
from preprocessing.extract_structural_entities import extract_code_entities

class TestRubyParser(unittest.TestCase):
    def test_ruby_extraction(self):
        example_path = Path(__file__).parent / "example.rb"
        with open(example_path, "rb") as f:
            code = f.read().replace(b"\r\n", b"\n")
        entities = extract_code_entities(code, ".rb")
        
        names = [e["name"] for e in entities]
        
        expected = [
            "Greeter",
            "Greeter::initialize",
            "Greeter::say_hello",
            "Greeter::greet_all",
            "MathUtils",
            "MathUtils::add"
        ]
        
        for name in expected:
            self.assertTrue(any(name in n for n in names), f"Missing {name} in {names}")

if __name__ == "__main__":
    unittest.main()
