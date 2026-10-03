import sqlite3
import unittest
from unittest.mock import patch

from app.infrastructure.db.repositories import (
    ConversationRepository,
    MemoryGraphRepository,
    MessageRepository,
)
from app.services.memory_graph_service import MemoryGraphService


class MemoryGraphTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(
            """
            CREATE TABLE conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model TEXT,
                sources TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE memory_nodes (
                id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                source_conversation_id INTEGER,
                source_message_id INTEGER,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE memory_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES memory_nodes(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES memory_nodes(id) ON DELETE CASCADE,
                UNIQUE(source_id, target_id, relation)
            );
            """
        )
        self.conv_repo = ConversationRepository()
        self.msg_repo = MessageRepository()
        self.graph_repo = MemoryGraphRepository()
        self.service = MemoryGraphService()

    def tearDown(self):
        self.conn.close()

    def test_create_and_get_node(self):
        node = self.graph_repo.create_node(
            self.conn,
            node_id="test_node_1",
            node_type="message",
            title="Sample Title",
            content="Sample Content",
            metadata={"importance": "high"},
        )
        self.assertEqual(node["id"], "test_node_1")
        self.assertEqual(node["title"], "Sample Title")
        self.assertEqual(node["metadata"]["importance"], "high")

        fetched = self.graph_repo.get_node(self.conn, "test_node_1")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["content"], "Sample Content")

    def test_capture_message_service(self):
        conv = self.conv_repo.create(self.conn, "Test Chat")
        msg = self.msg_repo.add(self.conn, conv["id"], "assistant", "Use async/await for I/O")

        with patch("app.services.memory_graph_service.get_connection") as mock_conn:
            mock_conn.return_value.__enter__.return_value = self.conn
            node = self.service.capture_message(conv["id"], msg["id"], title="Async I/O Tip")

        self.assertEqual(node["node_type"], "message")
        self.assertEqual(node["title"], "Async I/O Tip")
        self.assertEqual(node["content"], "Use async/await for I/O")
        self.assertEqual(node["source_conversation_id"], conv["id"])

    def test_capture_thread_creates_follows_edges(self):
        conv = self.conv_repo.create(self.conn, "Thread Chat")
        m1 = self.msg_repo.add(self.conn, conv["id"], "user", "What is JWT?")
        m2 = self.msg_repo.add(self.conn, conv["id"], "assistant", "JWT is JSON Web Token")
        m3 = self.msg_repo.add(self.conn, conv["id"], "user", "How to sign it?")
        m4 = self.msg_repo.add(self.conn, conv["id"], "assistant", "Use RS256 with private key")

        with patch("app.services.memory_graph_service.get_connection") as mock_conn:
            mock_conn.return_value.__enter__.return_value = self.conn
            result = self.service.capture_thread(conv["id"], title="JWT Discussion")

        nodes = result["nodes"]
        edges = result["edges"]

        self.assertEqual(len(nodes), 4)
        self.assertEqual(len(edges), 3)  # 3 follows edges between 4 turns
        for edge in edges:
            self.assertEqual(edge["relation"], "follows")

        # Verify edge sequence
        self.assertEqual(edges[0]["source_id"], nodes[0]["id"])
        self.assertEqual(edges[0]["target_id"], nodes[1]["id"])
        self.assertEqual(edges[1]["source_id"], nodes[1]["id"])
        self.assertEqual(edges[1]["target_id"], nodes[2]["id"])
        self.assertEqual(edges[2]["source_id"], nodes[2]["id"])
        self.assertEqual(edges[2]["target_id"], nodes[3]["id"])

    def test_custom_relates_to_edge(self):
        n1 = self.graph_repo.create_node(self.conn, "n1", "concept", "Auth", "JWT Auth")
        n2 = self.graph_repo.create_node(self.conn, "n2", "concept", "Security", "Key Rotation")

        with patch("app.services.memory_graph_service.get_connection") as mock_conn:
            mock_conn.return_value.__enter__.return_value = self.conn
            edge = self.service.create_edge("n1", "n2", relation="relates_to")

        self.assertEqual(edge["source_id"], "n1")
        self.assertEqual(edge["target_id"], "n2")
        self.assertEqual(edge["relation"], "relates_to")

    def test_delete_node_cascades_edges(self):
        self.graph_repo.create_node(self.conn, "n1", "concept", "A", "Content A")
        self.graph_repo.create_node(self.conn, "n2", "concept", "B", "Content B")
        self.graph_repo.create_edge(self.conn, "n1", "n2", "relates_to")

        self.assertEqual(len(self.graph_repo.list_edges(self.conn)), 1)
        self.graph_repo.delete_node(self.conn, "n1")

        self.assertIsNone(self.graph_repo.get_node(self.conn, "n1"))
        self.assertEqual(len(self.graph_repo.list_edges(self.conn)), 0)

    def test_compile_context(self):
        self.graph_repo.create_node(self.conn, "n1", "concept", "JWT Spec", "Token expires in 15m")
        self.graph_repo.create_node(self.conn, "n2", "concept", "Refresh Token", "Stored in HttpOnly cookie")
        self.graph_repo.create_edge(self.conn, "n1", "n2", "relates_to")

        context = self.service.compile_context(self.conn, ["n1"], depth=1)
        self.assertIn("Relevant background memory graph context", context)
        self.assertIn("JWT Spec", context)
        self.assertIn("Refresh Token", context)
    def test_api_endpoints_workflow(self):
        from fastapi.testclient import TestClient
        from main import app
        import database

        client = TestClient(app)

        # 1. Create conversation and messages
        conv = database.create_conversation("API Test Chat")
        cid = conv["id"]
        m1 = database.add_message(cid, "user", "How to use SQLite?")
        m2 = database.add_message(cid, "assistant", "Use python sqlite3 library with WAL mode")
        
        # 2. Capture single message
        res = client.post(
            "/memories/capture/message",
            json={"conversation_id": cid, "message_id": m2["id"], "title": "SQLite WAL Tip"}
        )
        self.assertEqual(res.status_code, 200)
        node_1 = res.json()["node"]
        self.assertEqual(node_1["node_type"], "message")
        self.assertEqual(node_1["title"], "SQLite WAL Tip")

        # 3. Capture thread
        res = client.post(
            "/memories/capture/thread",
            json={"conversation_id": cid, "up_to_message_id": m2["id"], "title": "SQLite Thread"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data["nodes"]), 2)
        self.assertEqual(len(data["edges"]), 1)
        self.assertEqual(data["edges"][0]["relation"], "follows")

        # 4. Create custom relates_to edge
        thread_node_id = data["nodes"][0]["id"]
        res = client.post(
            "/memories/edges",
            json={"source_id": node_1["id"], "target_id": thread_node_id, "relation": "relates_to"}
        )
        self.assertEqual(res.status_code, 200)
        edge = res.json()["edge"]
        self.assertEqual(edge["relation"], "relates_to")

        # 5. Get full graph
        res = client.get("/memories/graph")
        self.assertEqual(res.status_code, 200)
        graph = res.json()
        self.assertTrue(any(n["id"] == node_1["id"] for n in graph["nodes"]))
        self.assertTrue(any(e["id"] == edge["id"] for e in graph["edges"]))

        # 6. Delete edge
        res = client.delete(f"/memories/edges/{edge['id']}")
        self.assertEqual(res.status_code, 200)

        # 7. Delete node
        res = client.delete(f"/memories/{node_1['id']}")
        self.assertEqual(res.status_code, 200)

        # Cleanup conversation
        database.delete_conversation(cid)


if __name__ == "__main__":
    unittest.main()
