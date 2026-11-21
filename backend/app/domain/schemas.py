from typing import List, Literal, Optional

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
    # Keep API callers backward compatible; the frontend sends its explicit toggle state.
    tinyfish_enabled: bool = True


class Settings(BaseModel):
    enable_thinking: bool = False
    reasoning_budget: int = 8192
    obsidian_api_address: str = "https://127.0.0.1:27124"
    obsidian_api_key: str = ""
    obsidian_verify_tls: bool = True
    obsidian_ca_path: str = ""
    obsidian_allowed_folder: str = "BuddyAI/"
    obsidian_display_name: str = ""
    obsidian_allow_read: bool = True
    obsidian_allow_write: bool = True
    obsidian_allow_delete: bool = False


class ObsidianActionRequest(BaseModel):
    action: Literal["search", "open", "create", "append", "edit", "replace", "delete"]
    path: Optional[str] = None
    section: Optional[str] = None
    content: Optional[str] = None
    query: Optional[str] = None
    reason: Optional[str] = None
    if_match: Optional[str] = None


class ObsidianSearchRequest(BaseModel):
    query: str
    max_results: int = 20


class ObsidianConnectionTestRequest(BaseModel):
    api_address: Optional[str] = None
    api_key: Optional[str] = None
    verify_tls: bool = True
    ca_path: str = ""


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
    relation: Literal["relates_to", "references", "derived_from", "follows"] = "relates_to"
    metadata: Optional[dict] = None
