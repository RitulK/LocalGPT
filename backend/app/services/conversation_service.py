import database


def list_conversations() -> dict:
    conversations = database.list_conversations()
    for conversation in conversations:
        conversation["messages"] = database.list_messages(conversation["id"])
    return {"conversations": conversations}


def create_conversation(title: str) -> dict:
    conversation = database.create_conversation(title)
    conversation["messages"] = []
    return {"conversation": conversation}


def get_conversation(conversation_id: int) -> dict:
    conversation = database.get_conversation(conversation_id)
    if not conversation:
        return None
    conversation["messages"] = database.list_messages(conversation_id)
    return {"conversation": conversation}


def delete_conversation(conversation_id: int) -> bool:
    return database.delete_conversation(conversation_id)


def clear_conversation(conversation_id: int) -> bool:
    if not database.get_conversation(conversation_id):
        return False
    database.clear_messages(conversation_id)
    return True
