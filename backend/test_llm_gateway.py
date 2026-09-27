import unittest
from unittest.mock import AsyncMock, patch, MagicMock

from app.domain.models import ContentEvent, ReasoningEvent
from app.infrastructure.llm.gateway import LLMGateway, parse_model_spec
from langchain_core.messages import AIMessageChunk


class LLMGatewayTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.gateway = LLMGateway()

    def test_parse_model_spec(self):
        self.assertEqual(parse_model_spec("ollama:qwen:4b"), ("ollama", "qwen:4b", None))
        self.assertEqual(
            parse_model_spec("openai:llama-3.3@http://localhost:8000/v1"),
            ("openai", "llama-3.3", "http://localhost:8000/v1"),
        )
        self.assertEqual(
            parse_model_spec("nvidia:nvidia/nemotron-4-34b"),
            ("nvidia", "nvidia/nemotron-4-34b", None),
        )
        self.assertEqual(parse_model_spec("qwen:4b"), ("ollama", "qwen:4b", None))

    def test_get_client_creates_correct_provider(self):
        ollama_client = self.gateway._get_client("ollama:qwen:4b")
        self.assertEqual(ollama_client.model, "qwen:4b")

        vllm_client = self.gateway._get_client("vllm:llama-3.3-nemotron")
        self.assertEqual(vllm_client.model_name, "llama-3.3-nemotron")

        nvidia_client = self.gateway._get_client("nvidia:nvidia/nemotron-4-34b")
        self.assertEqual(nvidia_client.model_name, "nvidia/nemotron-4-34b")

    @patch.object(LLMGateway, "_get_client")
    async def test_stream_chat_streams_typed_events(self, mock_get_client):
        mock_client = MagicMock()

        async def fake_astream(messages):
            yield AIMessageChunk(content="", additional_kwargs={"reasoning_content": "Thinking..."})
            yield AIMessageChunk(content="Hello")
            yield AIMessageChunk(content=" world!")

        mock_client.astream.side_effect = fake_astream
        mock_get_client.return_value = mock_client

        messages = [{"role": "user", "content": "Hi"}]
        events = []
        async for event in self.gateway.stream_chat("ollama:qwen:4b", messages):
            events.append(event)

        self.assertEqual(len(events), 3)
        self.setIsInstance(events[0], ReasoningEvent) if hasattr(self, 'setIsInstance') else self.assertIsInstance(events[0], ReasoningEvent)
        self.assertEqual(events[0].content, "Thinking...")
        self.assertIsInstance(events[1], ContentEvent)
        self.assertEqual(events[1].content, "Hello")

    @patch("app.infrastructure.llm.gateway.OllamaEmbeddings")
    async def test_embed_calls_ollama_embeddings(self, mock_embeddings_cls):
        mock_embeddings_inst = MagicMock()
        mock_embeddings_inst.aembed_documents = AsyncMock(return_value=[[0.1, 0.2]])
        mock_embeddings_cls.return_value = mock_embeddings_inst

        result = await self.gateway.embed("ollama:nomic-embed-text", ["test prompt"])
        self.assertEqual(result, [[0.1, 0.2]])
        mock_embeddings_inst.aembed_documents.assert_called_once_with(["test prompt"])


if __name__ == "__main__":
    unittest.main()
