from app.infrastructure.db.connection import get_connection
from app.infrastructure.db.repositories import ConversationRepository, MessageRepository

conversation_repo = ConversationRepository()
message_repo = MessageRepository()


def list_conversations() -> dict:
    with get_connection() as conn:
        conversations = conversation_repo.list_all(conn)
        for conversation in conversations:
            conversation["messages"] = message_repo.list_by_conversation(conn, conversation["id"])
        return {"conversations": conversations}


def create_conversation(title: str) -> dict:
    with get_connection() as conn:
        conversation = conversation_repo.create(conn, title)
        conversation["messages"] = []
        return {"conversation": conversation}


def get_conversation(conversation_id: int) -> dict:
    with get_connection() as conn:
        conversation = conversation_repo.get(conn, conversation_id)
        if not conversation:
            return None
        conversation["messages"] = message_repo.list_by_conversation(conn, conversation_id)
        return {"conversation": conversation}


def delete_conversation(conversation_id: int) -> bool:
    with get_connection() as conn:
        return conversation_repo.delete(conn, conversation_id)


def clear_conversation(conversation_id: int) -> bool:
    with get_connection() as conn:
        if not conversation_repo.get(conn, conversation_id):
            return False
        message_repo.delete_by_conversation(conn, conversation_id)
        return True
