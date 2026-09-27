import unittest
from unittest.mock import AsyncMock, patch, MagicMock

from app.infrastructure.llm.gateway import LLMGateway
from langchain_core.messages import AIMessageChunk


class LLMGatewayTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.gateway = LLMGateway()

    def test_get_client_creates_correct_provider(self):
        ollama_client = self.gateway._get_client("ollama", "qwen:4b")
        self.assertEqual(ollama_client.model, "qwen:4b")

        vllm_client = self.gateway._get_client("vllm", "llama-3.3-nemotron")
        self.assertEqual(vllm_client.model_name, "llama-3.3-nemotron")

        nvidia_client = self.gateway._get_client("nvidia", "nvidia/nemotron-4-34b")
        self.assertEqual(nvidia_client.model_name, "nvidia/nemotron-4-34b")

    @patch.object(LLMGateway, "_get_client")
    async def test_stream_chat_streams_chunks(self, mock_get_client):
        mock_client = MagicMock()

        async def fake_astream(messages):
            yield AIMessageChunk(content="Hello")
            yield AIMessageChunk(content=" world!")

        mock_client.astream.side_effect = fake_astream
        mock_get_client.return_value = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        chunks = []
        async for chunk in self.gateway.stream_chat("ollama", "qwen:4b", messages):
            chunks.append(chunk)

        self.assertEqual(chunks, ["Hello", " world!"])

    @patch("app.infrastructure.llm.gateway.OllamaEmbeddings")
    async def test_embed_calls_ollama_embeddings(self, mock_embeddings_cls):
        mock_embeddings_inst = MagicMock()
        mock_embeddings_inst.aembed_documents = AsyncMock(return_value=[[0.1, 0.2]])
        mock_embeddings_cls.return_value = mock_embeddings_inst

        result = await self.gateway.embed("nomic-embed-text", ["test prompt"])
        self.assertEqual(result, [[0.1, 0.2]])
        mock_embeddings_inst.aembed_documents.assert_called_once_with(["test prompt"])


if __name__ == "__main__":
    unittest.main()
