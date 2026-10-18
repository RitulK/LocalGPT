from typing import Any, Dict, List, Literal, Union
from pydantic import BaseModel, Field


class MetadataEvent(BaseModel):
    type: Literal["metadata"] = "metadata"
    model: str
    conversation_id: int
    rag_used: bool = False
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    memories_used: List[str] = Field(default_factory=list)
    thinking_enabled: bool = False


class ContentEvent(BaseModel):
    type: Literal["content"] = "content"
    content: str


class ReasoningEvent(BaseModel):
    type: Literal["reasoning"] = "reasoning"
    content: str


class ToolCallEvent(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    tool_call_id: str
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolResultEvent(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool_call_id: str
    name: str
    result: Dict[str, Any] = Field(default_factory=dict)


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    error: str


StreamEvent = Union[
    MetadataEvent, ContentEvent, ReasoningEvent, ToolCallEvent,
    ToolResultEvent, DoneEvent, ErrorEvent
]
