import database


def list_memories():
    return {"memories": database.list_memories()}


def create_memory(kind: str, content: str, source: str):
    return {"memory": database.create_memory(kind, content, source)}


def delete_memory(memory_id: int) -> bool:
    return database.delete_memory(memory_id)
