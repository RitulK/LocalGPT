import unittest
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi.testclient import TestClient

from main import app
from app.services.chat_service import ChatService
from app.domain.schemas import ChatRequest


class ChatServiceTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.service = ChatService()

    def test_chat_service_public_methods(self):
        public_methods = [
            m for m in dir(ChatService) if not m.startswith("_")
        ]
        self.assertEqual(public_methods, ["stream_chat"])

    @patch("app.services.chat_service.ollama_client")
    async def test_stream_chat_missing_model_raises_value_error(self, mock_ollama):
        request = ChatRequest(prompt="Hello", use_router=False)
        with self.assertRaises(ValueError) as ctx:
            gen = self.service.stream_chat(request)
            await anext(gen)
        self.assertIn("Model must be specified", str(ctx.exception))

    @patch("app.services.chat_service.conversation_repo")
    @patch("app.services.chat_service.settings_repo")
    async def test_stream_chat_invalid_conversation_id_raises_value_error(self, mock_settings_repo, mock_conv_repo):
        mock_settings_repo.get.return_value = {}
        mock_conv_repo.get.return_value = None
        request = ChatRequest(prompt="Hello", model="ollama/qwen:4b")
        with self.assertRaises(ValueError) as ctx:
            gen = self.service.stream_chat(request, conversation_id=999999)
            await anext(gen)
        self.assertIn("Conversation not found", str(ctx.exception))

    @patch("app.services.chat_service.message_repo")
    @patch("app.services.chat_service.conversation_repo")
    @patch("app.services.chat_service.settings_repo")
    @patch("app.services.chat_service.ollama_client")
    async def test_stream_chat_yields_events(self, mock_ollama, mock_settings_repo, mock_conv_repo, mock_msg_repo):
        mock_settings_repo.get.return_value = {}
        mock_conv_repo.create.return_value = {"id": 1}
        mock_conv_repo.get.return_value = {"id": 1, "title": "Chat"}
        mock_msg_repo.list_by_conversation.return_value = []
        
        async def dummy_stream(*args, **kwargs):
            yield "Hello"
            yield " World"

        mock_ollama.chat_stream.side_effect = dummy_stream

        request = ChatRequest(prompt="Hi", model="ollama/qwen:4b")
        chunks = []
        async for item in self.service.stream_chat(request, conversation_id=1):
            chunks.append(item)

        self.assertGreater(len(chunks), 0)
        self.assertTrue(any("metadata" in chunk for chunk in chunks))
        self.assertTrue(any("done" in chunk for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
