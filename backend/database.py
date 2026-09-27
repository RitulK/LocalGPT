from typing import Any, Dict, List, Optional
from app.infrastructure.db.connection import DB_PATH, get_connection, init_db
from app.infrastructure.db.repositories import (
    ConversationRepository,
    DocumentRepository,
    MemoryRepository,
    MessageRepository,
    SettingsRepository,
    row_to_dict,
    utc_now,
)

conversation_repo = ConversationRepository()
message_repo = MessageRepository()
settings_repo = SettingsRepository()
memory_repo = MemoryRepository()
document_repo = DocumentRepository()


def list_conversations() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        return conversation_repo.list_all(conn)


def create_conversation(title: str = "New Chat") -> Dict[str, Any]:
    with get_connection() as conn:
        return conversation_repo.create(conn, title)


def get_conversation(conversation_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        return conversation_repo.get(conn, conversation_id)


def delete_conversation(conversation_id: int) -> bool:
    with get_connection() as conn:
        return conversation_repo.delete(conn, conversation_id)


def update_conversation_title(conversation_id: int, title: str) -> None:
    with get_connection() as conn:
        conversation_repo.update_title(conn, conversation_id, title)


def list_messages(conversation_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        return message_repo.list_by_conversation(conn, conversation_id)


def add_message(
    conversation_id: int,
    role: str,
    content: str,
    model: Optional[str] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    with get_connection() as conn:
        return message_repo.add(conn, conversation_id, role, content, model, sources)


def clear_messages(conversation_id: int) -> None:
    with get_connection() as conn:
        message_repo.delete_by_conversation(conn, conversation_id)


def get_settings(defaults: Dict[str, Any]) -> Dict[str, Any]:
    with get_connection() as conn:
        return settings_repo.get(conn, defaults)


def save_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    with get_connection() as conn:
        return settings_repo.save(conn, settings)


def list_memories() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        return memory_repo.list_all(conn)


def create_memory(kind: str, content: str, source: Optional[str] = None) -> Dict[str, Any]:
    with get_connection() as conn:
        return memory_repo.create(conn, kind, content, source)


def delete_memory(memory_id: int) -> bool:
    with get_connection() as conn:
        return memory_repo.delete(conn, memory_id)


def create_document(
    filename: str,
    content_type: str,
    file_path: str,
    status: str = "pending",
) -> Dict[str, Any]:
    with get_connection() as conn:
        return document_repo.create(conn, filename, content_type, file_path, status)


def update_document_file_path(document_id: int, file_path: str) -> None:
    with get_connection() as conn:
        document_repo.update_file_path(conn, document_id, file_path)


def update_document_status(
    document_id: int,
    status: str,
    chunk_count: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    with get_connection() as conn:
        document_repo.update_status(conn, document_id, status, chunk_count, error)


def get_document(document_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        return document_repo.get(conn, document_id)


def list_documents() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        return document_repo.list_all(conn)


def delete_document(document_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        return document_repo.delete(conn, document_id)


def replace_document_chunks(document_id: int, chunks: List[Dict[str, Any]]) -> None:
    with get_connection() as conn:
        document_repo.replace_chunks(conn, document_id, chunks)


def list_document_chunks(document_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        return document_repo.list_chunks(conn, document_id)
