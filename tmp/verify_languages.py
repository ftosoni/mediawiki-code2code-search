import sys
import os

# Add current directory to path if needed
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from build import extract_functions_treesitter

TEST_CASES = {
    ".py": b"def hello():\n    print('hello')\n\nclass X:\n    def method(self):\n        pass",
    ".php": b"<?php\nfunction hello_php() {\n    echo 'hello';\n}\n\nclass User {\n    public function login() {}\n}",
    ".js": b"function hello_js() {}\n\nconst obj = {\n    method_js() {}\n}",
    ".ts": b"function hello_ts(name: string): void {}\n\nclass Device {\n    powerOn() {}\n}",
    ".lua": b"function hello_lua()\n    print('hello')\nend",
    ".go": b"func hello_go() {}\n\ntype S struct{}\nfunc (s *S) method_go() {}",
    ".java": b"public class App {\n    public static void main(String[] args) {}\n    private int getData() { return 1; }\n}",
    ".rs": b"fn hello_rust() {}\n\nimpl Data {\n    fn new() -> Self {}\n}"
}

def verify():
    print("== Tree-sitter Multi-Language Extraction Verification ==")
    success = True
    for ext, code in TEST_CASES.items():
        print(f"Testing {ext}...")
        try:
            functions = extract_functions_treesitter(code, ext)
            if functions:
                print(f"  ✅ Extracted {len(functions)} functions:")
                for fn in functions:
                    print(f"    - {fn['name']} (Lines {fn['start_line']}-{fn['end_line']})")
            else:
                print(f"  ❌ No functions extracted for {ext}")
                success = False
        except Exception as e:
            print(f"  💥 Error extracting {ext}: {e}")
            success = False
        print("-" * 40)
    
    if success:
        print("✅ All language parsers verified successfully.")
    else:
        print("❌ Some parsers failed verification.")

if __name__ == "__main__":
    verify()
