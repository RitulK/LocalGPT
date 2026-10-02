import sqlite3
import unittest

from app.infrastructure.db.connection import init_db
from app.infrastructure.db.repositories import (
    ConversationRepository,
    DocumentRepository,
    MemoryRepository,
    MessageRepository,
    SettingsRepository,
)


class RepositoriesTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Initialize schema in memory connection
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
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                model TEXT,
                sources TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
            CREATE TABLE settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL DEFAULT 'note',
                content TEXT NOT NULL,
                source TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                chunk_count INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                page_number INTEGER,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );
            """
        )

        self.conv_repo = ConversationRepository()
        self.msg_repo = MessageRepository()
        self.settings_repo = SettingsRepository()
        self.memory_repo = MemoryRepository()
        self.doc_repo = DocumentRepository()

    def tearDown(self):
        self.conn.close()

    def test_conversation_and_message_repository(self):
        conv = self.conv_repo.create(self.conn, "Test Chat")
        self.assertEqual(conv["title"], "Test Chat")
        
        fetched = self.conv_repo.get(self.conn, conv["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["title"], "Test Chat")

        msg = self.msg_repo.add(self.conn, conv["id"], "user", "Hello")
        self.assertEqual(msg["content"], "Hello")

        messages = self.msg_repo.list_by_conversation(self.conn, conv["id"])
        self.assertEqual(len(messages), 1)

        self.conv_repo.update_title(self.conn, conv["id"], "Updated Title")
        updated_conv = self.conv_repo.get(self.conn, conv["id"])
        self.assertEqual(updated_conv["title"], "Updated Title")

        self.msg_repo.delete_by_conversation(self.conn, conv["id"])
        messages_after_delete = self.msg_repo.list_by_conversation(self.conn, conv["id"])
        self.assertEqual(len(messages_after_delete), 0)

        self.assertTrue(self.conv_repo.delete(self.conn, conv["id"]))

    def test_settings_repository(self):
        defaults = {"enable_thinking": True}
        settings = self.settings_repo.get(self.conn, defaults)
        self.assertEqual(settings, defaults)

        self.settings_repo.save(self.conn, {"enable_thinking": False, "theme": "dark"})
        saved = self.settings_repo.get(self.conn, defaults)
        self.assertFalse(saved["enable_thinking"])
        self.assertEqual(saved["theme"], "dark")

    def test_memory_repository(self):
        mem = self.memory_repo.create(self.conn, "note", "Remember milk")
        self.assertEqual(mem["content"], "Remember milk")

        memories = self.memory_repo.list_all(self.conn)
        self.assertEqual(len(memories), 1)

        self.assertTrue(self.memory_repo.delete(self.conn, mem["id"]))
        self.assertEqual(len(self.memory_repo.list_all(self.conn)), 0)

    def test_document_repository(self):
        doc = self.doc_repo.create(self.conn, "test.pdf", "application/pdf", "/tmp/test.pdf")
        self.assertEqual(doc["filename"], "test.pdf")

        self.doc_repo.update_status(self.conn, doc["id"], "ready", chunk_count=5)
        updated_doc = self.doc_repo.get(self.conn, doc["id"])
        self.assertEqual(updated_doc["status"], "ready")
        self.assertEqual(updated_doc["chunk_count"], 5)

        chunks = [{"chunk_index": 0, "content": "chunk 1", "page_number": 1}]
        self.doc_repo.replace_chunks(self.conn, doc["id"], chunks)
        saved_chunks = self.doc_repo.list_chunks(self.conn, doc["id"])
        self.assertEqual(len(saved_chunks), 1)
        self.assertEqual(saved_chunks[0]["content"], "chunk 1")

        deleted = self.doc_repo.delete(self.conn, doc["id"])
        self.assertIsNotNone(deleted)


if __name__ == "__main__":
    unittest.main()
