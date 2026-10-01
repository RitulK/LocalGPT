import tempfile
import unittest
from pathlib import Path

from app.infrastructure.vector.chroma_store import ChromaStore
from langchain_core.retrievers import BaseRetriever


class ChromaStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.chroma_path = Path(self.temp_dir.name)
        self.store = ChromaStore(chroma_dir=self.chroma_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_chroma_store_initialization(self):
        collection = self.store.get_collection()
        self.assertEqual(collection.name, "localgpt_documents")

    def test_as_retriever_returns_retriever_with_single_document_id(self):
        retriever = self.store.as_retriever(document_ids=[42], k=3)
        self.assertIsInstance(retriever, BaseRetriever)
        self.assertEqual(retriever.search_kwargs["k"], 3)
        self.assertEqual(retriever.search_kwargs["filter"], {"document_id": 42})

    def test_as_retriever_returns_retriever_with_multiple_document_ids(self):
        retriever = self.store.as_retriever(document_ids=[10, 20], k=5)
        self.assertIsInstance(retriever, BaseRetriever)
        self.assertEqual(retriever.search_kwargs["k"], 5)
        self.assertEqual(retriever.search_kwargs["filter"], {"document_id": {"$in": [10, 20]}})


if __name__ == "__main__":
    unittest.main()
