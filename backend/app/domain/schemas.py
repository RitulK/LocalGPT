from typing import List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    conversation_id: Optional[int] = None
    conversation_history: Optional[List[dict]] = None
    use_rag: bool = False
    document_ids: Optional[List[int]] = None
    enable_thinking: bool = False
    reasoning_budget: int = 8192


class Settings(BaseModel):
    enable_thinking: bool = False
    reasoning_budget: int = 8192


class ConversationCreate(BaseModel):
    title: str = "New Chat"


class MemoryCreate(BaseModel):
    kind: str = "note"
    content: str
    source: Optional[str] = None
