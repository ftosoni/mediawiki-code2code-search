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
