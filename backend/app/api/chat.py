from fastapi import APIRouter

from app.domain.schemas import ChatRequest
from app.services.chat_service import chat as handle_chat

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    return await handle_chat(request)
