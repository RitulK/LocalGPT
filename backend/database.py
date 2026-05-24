import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_PATH = Path(__file__).resolve().parent / "localgpt.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row)


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                model TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL DEFAULT 'note',
                content TEXT NOT NULL,
                source TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
                ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_memories_kind
                ON memories(kind);
            """
        )


def list_conversations() -> List[Dict[str, Any]]:
    with get_connection() as conn:
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


def create_conversation(title: str = "New Chat") -> Dict[str, Any]:
    now = utc_now()
    with get_connection() as conn:
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


def get_conversation(conversation_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        return row_to_dict(row) if row else None


def delete_conversation(conversation_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        return cursor.rowcount > 0


def update_conversation_title(conversation_id: int, title: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, utc_now(), conversation_id),
        )


def list_messages(conversation_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, conversation_id, role, content, model, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        ).fetchall()
        return [row_to_dict(row) for row in rows]


def add_message(
    conversation_id: int,
    role: str,
    content: str,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    now = utc_now()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content, model, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conversation_id, role, content, model, now),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        row = conn.execute(
            "SELECT * FROM messages WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return row_to_dict(row)


def clear_messages(conversation_id: int) -> None:
    with get_connection() as conn:
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


def get_settings(defaults: Dict[str, Any]) -> Dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'app_settings'"
        ).fetchone()
        if not row:
            return defaults
        return {**defaults, **json.loads(row["value"])}


def save_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    now = utc_now()
    with get_connection() as conn:
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


def list_memories() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, kind, content, source, created_at, updated_at
            FROM memories
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [row_to_dict(row) for row in rows]


def create_memory(kind: str, content: str, source: Optional[str] = None) -> Dict[str, Any]:
    now = utc_now()
    with get_connection() as conn:
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


def delete_memory(memory_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM memories WHERE id = ?",
            (memory_id,),
        )
        return cursor.rowcount > 0
