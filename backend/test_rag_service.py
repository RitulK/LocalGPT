import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from rag_service import RAGService


class RAGServiceTest(unittest.IsolatedAsyncioTestCase):
    def test_txt_extraction_normalizes_whitespace(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.txt"
            path.write_text("alpha\n\n beta\tgamma")

            pages = RAGService(base_dir=Path(directory)).extract_text(path)

        self.assertEqual(pages, [{"page_number": None, "text": "alpha beta gamma"}])

    def test_chunk_pages_uses_overlap(self):
        service = RAGService()
        pages = [
            {
                "page_number": 3,
                "text": "one two three four five six seven eight nine ten",
            }
        ]

        chunks = service.chunk_pages(pages, chunk_words=5, overlap_words=2)

        self.assertEqual(chunks[0]["content"], "one two three four five")
        self.assertEqual(chunks[1]["content"], "four five six seven eight")
        self.assertEqual(chunks[0]["page_number"], 3)
        self.assertEqual(chunks[1]["chunk_index"], 1)

    async def test_retrieve_skips_documents_that_are_not_ready(self):
        service = RAGService()
        ollama_client = AsyncMock()

        with patch("rag_service.database.get_document", return_value={"status": "failed"}):
            results = await service.retrieve("what is inside?", [42], ollama_client)

        self.assertEqual(results, [])
        ollama_client.embed.assert_not_called()


if __name__ == "__main__":
    unittest.main()
