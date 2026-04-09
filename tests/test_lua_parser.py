import unittest
import os
from pathlib import Path
from preprocessing.extract_structural_entities import extract_code_entities

class TestLuaParser(unittest.TestCase):
    def test_lua_extraction(self):
        example_path = Path(__file__).parent / "example.lua"
        with open(example_path, "rb") as f:
            code = f.read().replace(b"\r\n", b"\n")
        entities = extract_code_entities(code, ".lua")
        
        names = [e["name"] for e in entities]
        
        # Lua captures are simpler
        expected = [
            "Point:new", "Box", "functionWithLocalClass", 
            "functionWithLocalClass::LocalClass:add",
            "functionWithLocalClass::LocalClass:add::innerHelper",
            "Wrapper", "Wrapper::self::x::innerHelper"
        ]
        
        for name in expected:
            # Normalize BOTH for comparison to be robust
            norm_expected = name.replace("::", ":").replace(":", "::")
            self.assertTrue(any(norm_expected in n.replace("::", ":").replace(":", "::") for n in names), f"Missing {name} in {names}")

if __name__ == "__main__":
    unittest.main()
