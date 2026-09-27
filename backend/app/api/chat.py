from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.domain.schemas import ChatRequest
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        stream = chat_service.stream_chat(request, request.conversation_id)
        return StreamingResponse(
            stream,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc))
