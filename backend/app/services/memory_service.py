from app.infrastructure.db.connection import get_connection
from app.infrastructure.db.repositories import MemoryRepository

memory_repo = MemoryRepository()


def list_memories():
    with get_connection() as conn:
        return {"memories": memory_repo.list_all(conn)}


def create_memory(kind: str, content: str, source: str):
    with get_connection() as conn:
        return {"memory": memory_repo.create(conn, kind, content, source)}


def delete_memory(memory_id: int) -> bool:
    with get_connection() as conn:
        return memory_repo.delete(conn, memory_id)
