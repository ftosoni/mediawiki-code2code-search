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

import torch
import unittest
from models.jina_embeddings import JinaCodeEmbeddings
from models.cross_encoder_reranker import CrossEncoderReranker

class TestJinaComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {cls.device}")

    def test_jina_embeddings_normalization(self):
        model = JinaCodeEmbeddings(device=self.device)
        code = "def hello(): print('world')"
        emb = model.encode(code)
        
        # Check dimension (Jina 0.5b is 512)
        self.assertEqual(emb.shape[0], 512)
        
        # Check normalization (L2 norm should be ~1.0)
        norm = torch.norm(emb, p=2).item()
        self.assertAlmostEqual(norm, 1.0, places=5)
        print("Embeddings normalization test passed.")

    def test_jina_reranker_scoring(self):
        reranker = CrossEncoderReranker(device=self.device)
        query = "How to sort a list in Python?"
        candidates = [
            "my_list.sort()",
            "print('hello world')",
            "sorted_list = sorted(my_list)"
        ]
        
        scores = reranker.compute_scores(query, candidates)
        self.assertEqual(len(scores), 3)
        
        # The first and third should ideally have higher scores than the second
        self.assertTrue(scores[0] > scores[1])
        self.assertTrue(scores[2] > scores[1])
        print("Reranker scoring test passed.")

if __name__ == "__main__":
    unittest.main()
