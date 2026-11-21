import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from main import app


class APIRouteTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertLess(response.status_code, 500)

    def test_conversation_crud_routes(self):
        created = self.client.post("/conversations", json={"title": "Test chat"})
        self.assertEqual(created.status_code, 200)
        conversation = created.json()["conversation"]

        fetched = self.client.get(f"/conversations/{conversation['id']}")
        self.assertEqual(fetched.status_code, 200)

        deleted = self.client.delete(f"/conversations/{conversation['id']}")
        self.assertEqual(deleted.status_code, 200)

    @patch("app.api.documents.document_service")
    def test_document_status_and_delete_routes(self, mock_service):
        mock_service.list_documents.return_value = []
        response = self.client.get("/documents")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"documents": []})

        mock_service.get_document.return_value = {"id": 7, "status": "pending"}
        response = self.client.get("/documents/7")
        self.assertEqual(response.status_code, 200)

        mock_service.delete_document.return_value = True
        response = self.client.delete("/documents/7")
        self.assertEqual(response.status_code, 200)

    @patch("app.api.memories.memory_graph_service")
    def test_memory_graph_route(self, mock_service):
        mock_service.get_graph.return_value = {"nodes": [], "edges": []}
        response = self.client.get("/memories/graph")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"nodes": [], "edges": []})

    def test_settings_round_trip(self):
        response = self.client.get("/settings")
        self.assertEqual(response.status_code, 200)
        settings = response.json()

        response = self.client.post("/settings", json=settings)
        self.assertIn(response.status_code, (200, 422))

    @patch("app.api.obsidian.ObsidianService")
    def test_execute_returns_controlled_error_for_httpx_failure(self, mock_service):
        mock_service.return_value.execute = AsyncMock(
            side_effect=httpx.ConnectError("Obsidian is unavailable")
        )

        response = self.client.post(
            "/obsidian/execute",
            json={"action": "open", "path": "BuddyAI/Test.md"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Obsidian is unavailable", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
