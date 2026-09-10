from typing import List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    use_router: bool = False
    conversation_id: Optional[int] = None
    conversation_history: Optional[List[dict]] = None
    use_rag: bool = False
    document_ids: Optional[List[int]] = None
    enable_thinking: bool = False
    reasoning_budget: int = 8192


class Settings(BaseModel):
    default_general_model: Optional[str] = None
    default_coding_model: Optional[str] = None
    default_reasoning_model: Optional[str] = None
    router_enabled: bool = True
    router_models: Optional[List[str]] = None
    enable_thinking: bool = False
    reasoning_budget: int = 8192


class ConversationCreate(BaseModel):
    title: str = "New Chat"


class MemoryCreate(BaseModel):
    kind: str = "note"
    content: str
    source: Optional[str] = None
