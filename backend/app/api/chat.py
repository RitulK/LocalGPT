from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from app.core.limiter import limiter

from app.domain.schemas import ChatRequest
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/chat")
@limiter.limit("60/minute")
async def chat(request: Request, response: Response, chat_request: ChatRequest):
    try:
        chat_service.validate_request(chat_request, chat_request.conversation_id)
        stream = chat_service.stream_chat(chat_request, chat_request.conversation_id)
        return StreamingResponse(
            stream,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc))
