import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from main import app
from app.core.local_access import require_local_request


class APIRouteTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        app.dependency_overrides[require_local_request] = lambda: None

    def tearDown(self):
        app.dependency_overrides.clear()

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

    def test_remote_client_cannot_repoint_saved_obsidian_settings(self):
        settings_response = self.client.get("/settings")
        settings = settings_response.json()
        settings["obsidian_api_address"] = "https://127.0.0.1:9999"

        response = self.client.post("/settings", json=settings)

        self.assertEqual(response.status_code, 403)

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

    @patch("app.api.obsidian.ObsidianService")
    @patch("app.api.obsidian._generate_text", new_callable=AsyncMock)
    def test_confirm_proposal_route_uses_server_issued_proposal_once(self, mock_generate, mock_service):
        mock_generate.return_value = (
            '{"action":"create","title":"Test","path":"BuddyAI/Test.md",'
            '"content":"# Test","reason":"test"}'
        )
        mock_service.return_value.execute = AsyncMock(
            return_value={"action": "create", "created": True, "path": "BuddyAI/Test.md"}
        )

        proposal_response = self.client.post(
            "/obsidian/generate-proposal",
            json={"tool": "new_note", "model": "ollama:test", "prompt": "make a test note"},
        )
        self.assertEqual(proposal_response.status_code, 200)
        proposal = proposal_response.json()
        self.assertTrue(proposal["proposal_id"])

        response = self.client.post(
            "/obsidian/proposals/confirm",
            json={"proposal_id": proposal["proposal_id"], "content": "# Edited test"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["created"])
        self.assertEqual(
            mock_service.return_value.execute.await_args.args[0]["path"],
            "BuddyAI/Test.md",
        )
        self.assertEqual(
            mock_service.return_value.execute.await_args.args[0]["content"],
            "# Edited test",
        )

        repeated = self.client.post(
            "/obsidian/proposals/confirm",
            json={"proposal_id": proposal["proposal_id"], "content": "# Tampered"},
        )
        self.assertEqual(repeated.status_code, 404)
        self.assertEqual(mock_service.return_value.execute.await_count, 1)

    @patch("app.api.obsidian.ObsidianService")
    @patch("app.api.obsidian._generate_text", new_callable=AsyncMock)
    def test_generate_proposal_rejects_non_object_model_output(self, mock_generate, mock_service):
        mock_generate.return_value = '[{"action":"create","content":"# Note"}]'

        response = self.client.post(
            "/obsidian/generate-proposal",
            json={"tool": "new_note", "model": "ollama:test", "prompt": "make a test note"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("JSON proposal object", response.json()["detail"])
        mock_service.return_value.execute.assert_not_called()

    @patch("app.api.obsidian.ObsidianService")
    def test_direct_execute_cannot_write_without_proposal(self, mock_service):
        response = self.client.post(
            "/obsidian/execute",
            json={"action": "create", "path": "BuddyAI/Test.md", "content": "# Test"},
        )

        self.assertEqual(response.status_code, 400)
        mock_service.return_value.execute.assert_not_called()

    @patch("app.api.obsidian.get_saved_settings")
    @patch("app.api.obsidian.ObsidianService")
    def test_connection_test_rejects_external_host_before_forwarding_saved_key(
        self, mock_service, mock_get_settings
    ):
        mock_get_settings.return_value = {
            "obsidian_api_address": "https://127.0.0.1:27124",
            "obsidian_api_key": "do-not-forward",
            "obsidian_verify_tls": True,
            "obsidian_ca_path": "",
            "obsidian_display_name": "",
        }

        response = self.client.post(
            "/obsidian/test",
            json={"api_address": "http://attacker.example", "verify_tls": False},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("loopback", response.json()["detail"])
        mock_service.assert_not_called()

    def test_obsidian_routes_reject_remote_clients(self):
        request = Request({
            "type": "http",
            "method": "GET",
            "path": "/obsidian/status",
            "headers": [],
            "client": ("192.0.2.10", 50000),
            "server": ("127.0.0.1", 8000),
        })

        with self.assertRaises(HTTPException) as context:
            asyncio.run(require_local_request(request))
        self.assertEqual(context.exception.status_code, 403)

    def test_obsidian_routes_reject_non_local_origins(self):
        request = Request({
            "type": "http",
            "method": "GET",
            "path": "/obsidian/status",
            "headers": [(b"origin", b"https://untrusted.example")],
            "client": ("127.0.0.1", 50000),
            "server": ("127.0.0.1", 8000),
        })

        with self.assertRaises(HTTPException) as context:
            asyncio.run(require_local_request(request))
        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
