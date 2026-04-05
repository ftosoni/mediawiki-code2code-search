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
import tree_sitter_php

PHP_LANGUAGE = tree_sitter.Language(tree_sitter_php.language_php())
parser = tree_sitter.Parser(PHP_LANGUAGE)

code = b"""<?php
class MyClass {
    public function myMethod($a) {
        return $a;
    }
}

function myGlobalFunction() {
    echo "hello";
}
"""

tree = parser.parse(code)
query_scm = "(function_definition) @function (method_declaration) @function (class_declaration) @type"
query = tree_sitter.Query(PHP_LANGUAGE, query_scm)
cursor = tree_sitter.QueryCursor(query)
captures = cursor.captures(tree.root_node)

def extract_entity_name(node, code_bytes: bytes) -> str:
    name_node = node.child_by_field_name("name")
    if not name_node:
        def find_name(n):
            if n.type in ["identifier", "field_identifier", "type_identifier", "name"]:
                return n
            for child in n.children:
                found = find_name(child)
                if found: return found
            return None
        name_node = find_name(node)
    
    if name_node:
        return code_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8', errors='ignore')
    return "unknown"

for entity_type, nodes in captures.items():
    for node in nodes:
        print(f"Type: {entity_type}, Name: {extract_entity_name(node, code)}")
