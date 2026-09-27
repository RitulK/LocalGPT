import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row)


class ConversationRepository:
    def list_all(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT c.*,
                   COUNT(m.id) AS message_count,
                   MAX(m.created_at) AS last_message_at
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]

    def create(self, conn: sqlite3.Connection, title: str = "New Chat") -> Dict[str, Any]:
        now = utc_now()
        cursor = conn.execute(
            """
            INSERT INTO conversations (title, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            (title, now, now),
        )
        conversation_id = cursor.lastrowid
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        return row_to_dict(row)

    def get(self, conn: sqlite3.Connection, conversation_id: int) -> Optional[Dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        return row_to_dict(row) if row else None

    def delete(self, conn: sqlite3.Connection, conversation_id: int) -> bool:
        cursor = conn.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        return cursor.rowcount > 0

    def update_title(self, conn: sqlite3.Connection, conversation_id: int, title: str) -> None:
        conn.execute(
            """
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, utc_now(), conversation_id),
        )


class MessageRepository:
    def list_by_conversation(self, conn: sqlite3.Connection, conversation_id: int) -> List[Dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT id, conversation_id, role, content, model, sources, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()
        messages = []
        for row in rows:
            message = row_to_dict(row)
            message["sources"] = json.loads(message["sources"]) if message.get("sources") else []
            messages.append(message)
        return messages

    def add(
        self,
        conn: sqlite3.Connection,
        conversation_id: int,
        role: str,
        content: str,
        model: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        now = utc_now()
        cursor = conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content, model, sources, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                role,
                content,
                model,
                json.dumps(sources or []),
                now,
            ),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        row = conn.execute(
            "SELECT * FROM messages WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        message = row_to_dict(row)
        message["sources"] = json.loads(message["sources"]) if message.get("sources") else []
        return message

    def delete_by_conversation(self, conn: sqlite3.Connection, conversation_id: int) -> None:
        conn.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        conn.execute(
            """
            UPDATE conversations
            SET title = 'New Chat', updated_at = ?
            WHERE id = ?
            """,
            (utc_now(), conversation_id),
        )


class SettingsRepository:
    def get(self, conn: sqlite3.Connection, defaults: Dict[str, Any]) -> Dict[str, Any]:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'app_settings'"
        ).fetchone()
        if not row:
            return defaults
        return {**defaults, **json.loads(row["value"])}

    def save(self, conn: sqlite3.Connection, settings: Dict[str, Any]) -> Dict[str, Any]:
        now = utc_now()
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES ('app_settings', ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (json.dumps(settings), now),
        )
        return settings


class MemoryRepository:
    def list_all(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT id, kind, content, source, created_at, updated_at
            FROM memories
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]

    def create(self, conn: sqlite3.Connection, kind: str, content: str, source: Optional[str] = None) -> Dict[str, Any]:
        now = utc_now()
        cursor = conn.execute(
            """
            INSERT INTO memories (kind, content, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (kind, content, source, now, now),
        )
        row = conn.execute(
            "SELECT * FROM memories WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return row_to_dict(row)

    def delete(self, conn: sqlite3.Connection, memory_id: int) -> bool:
        cursor = conn.execute(
            "DELETE FROM memories WHERE id = ?",
            (memory_id,),
        )
        return cursor.rowcount > 0


class DocumentRepository:
    def create(
        self,
        conn: sqlite3.Connection,
        filename: str,
        content_type: str,
        file_path: str,
        status: str = "pending",
    ) -> Dict[str, Any]:
        now = utc_now()
        cursor = conn.execute(
            """
            INSERT INTO documents
                (filename, content_type, file_path, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (filename, content_type, file_path, status, now, now),
        )
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return row_to_dict(row)

    def update_file_path(self, conn: sqlite3.Connection, document_id: int, file_path: str) -> None:
        conn.execute(
            """
            UPDATE documents
            SET file_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (file_path, utc_now(), document_id),
        )

    def update_status(
        self,
        conn: sqlite3.Connection,
        document_id: int,
        status: str,
        chunk_count: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        assignments = ["status = ?", "updated_at = ?", "error = ?"]
        values: List[Any] = [status, utc_now(), error]
        if chunk_count is not None:
            assignments.append("chunk_count = ?")
            values.append(chunk_count)
        values.append(document_id)

        conn.execute(
            f"""
            UPDATE documents
            SET {", ".join(assignments)}
            WHERE id = ?
            """,
            values,
        )

    def get(self, conn: sqlite3.Connection, document_id: int) -> Optional[Dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        return row_to_dict(row) if row else None

    def list_all(self, conn: sqlite3.Connection) -> List[Dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT id, filename, content_type, file_path, status, chunk_count,
                   error, created_at, updated_at
            FROM documents
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]

    def delete(self, conn: sqlite3.Connection, document_id: int) -> Optional[Dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        if not row:
            return None
        conn.execute(
            "DELETE FROM documents WHERE id = ?",
            (document_id,),
        )
        return row_to_dict(row)

    def replace_chunks(self, conn: sqlite3.Connection, document_id: int, chunks: List[Dict[str, Any]]) -> None:
        now = utc_now()
        conn.execute(
            "DELETE FROM document_chunks WHERE document_id = ?",
            (document_id,),
        )
        conn.executemany(
            """
            INSERT INTO document_chunks
                (document_id, chunk_index, page_number, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    document_id,
                    chunk["chunk_index"],
                    chunk.get("page_number"),
                    chunk["content"],
                    now,
                )
                for chunk in chunks
            ],
        )

    def list_chunks(self, conn: sqlite3.Connection, document_id: int) -> List[Dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT id, document_id, chunk_index, page_number, content, created_at
            FROM document_chunks
            WHERE document_id = ?
            ORDER BY chunk_index ASC
            """,
            (document_id,),
        ).fetchall()
        return [row_to_dict(row) for row in rows]
