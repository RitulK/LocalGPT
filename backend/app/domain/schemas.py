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
    memory_node_ids: Optional[List[str]] = None


class Settings(BaseModel):
    enable_thinking: bool = False
    reasoning_budget: int = 8192


class ConversationCreate(BaseModel):
    title: str = "New Chat"


class MemoryCreate(BaseModel):
    kind: str = "note"
    content: str
    source: Optional[str] = None


class MessageCaptureRequest(BaseModel):
    conversation_id: int
    message_id: int
    title: Optional[str] = None


class ThreadCaptureRequest(BaseModel):
    conversation_id: int
    up_to_message_id: Optional[int] = None
    title: Optional[str] = None


class MemoryEdgeCreate(BaseModel):
    source_id: str
    target_id: str
    relation: str = "relates_to"
    metadata: Optional[dict] = None
