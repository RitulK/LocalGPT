from typing import Any, Dict, List, Literal, Union
from pydantic import BaseModel, Field


class MetadataEvent(BaseModel):
    type: Literal["metadata"] = "metadata"
    model: str
    routing_used: bool = False
    conversation_id: int
    rag_used: bool = False
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    thinking_enabled: bool = False


class ContentEvent(BaseModel):
    type: Literal["content"] = "content"
    content: str


class ReasoningEvent(BaseModel):
    type: Literal["reasoning"] = "reasoning"
    content: str


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    error: str


StreamEvent = Union[MetadataEvent, ContentEvent, ReasoningEvent, DoneEvent, ErrorEvent]
