# This file is part of MediaWiki Code2Code Search
# <https://github.com/ftosoni/mediawiki-code2code-search>.
# Copyright (c) 2026 Francesco Tosoni.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import tree_sitter
import tree_sitter_cpp
import os
import sys

# Add current directory to path so we can import from build.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from build import extract_code_entities

def test_cpp_template_extraction():
    code = """
    template <class Input>
    class MyClass {
    public:
        void f(Input a, Input b) {
            Input result = a + b;
            return;
        }
    };

    template<uint8_t MIN_L = 1, typename code_type = uint128_t, uint8_t MAX_L_THRS = MAX_L_THRS, uint8_t space_relaxation = 0>
    class Trie_lw {
    public:
        struct TrieNode_lw {
            TrieNode_lw() {
                isEndOfWord = false;
                l_idx = 0;
            }
        };
    };
    """
    
    entities = extract_code_entities(code.encode(), ".cpp")
    
    print(f"Extracted {len(entities)} entities:")
    for ent in entities:
        print(f"  [{ent['type']}] {ent['name']} (Lines {ent['start_line']}-{ent['end_line']})")

    # Assertions
    names = [e["name"] for e in entities]
    types = [e["type"] for e in entities]
    
    assert "MyClass" in names, "MyClass missing"
    assert "Trie_lw" in names, "Trie_lw missing"
    assert "f" in names, "Function f missing"
    
    # Check counts
    assert names.count("MyClass") == 1, f"MyClass extracted {names.count('MyClass')} times"
    assert names.count("Trie_lw") == 1, f"Trie_lw extracted {names.count('Trie_lw')} times"
    
    # Check types
    my_class = [e for e in entities if e["name"] == "MyClass"][0]
    assert my_class["type"] == "template_type", f"MyClass should be 'template_type', got '{my_class['type']}'"

    f_func = [e for e in entities if e["name"] == "f"][0]
    assert f_func["type"] == "function", f"f should be 'function', got '{f_func['type']}'"

    trie_lw = [e for e in entities if e["name"] == "Trie_lw"][0]
    assert trie_lw["type"] == "template_type", f"Trie_lw should be 'template_type', got '{trie_lw['type']}'"

    print("\n✅ All assertions passed!")

if __name__ == "__main__":
    try:
        test_cpp_template_extraction()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 An error occurred: {e}")
        sys.exit(1)
