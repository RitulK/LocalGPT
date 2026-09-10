from fastapi import APIRouter, HTTPException

from app.domain.schemas import ConversationCreate
from app.services import conversation_service

router = APIRouter()


@router.get("/conversations")
async def list_conversations():
    return conversation_service.list_conversations()


@router.post("/conversations")
async def create_conversation(request: ConversationCreate):
    return conversation_service.create_conversation(request.title)


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int):
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    if not conversation_service.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted"}


@router.delete("/conversations/{conversation_id}/messages")
async def clear_conversation(conversation_id: int):
    if not conversation_service.clear_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation cleared"}
