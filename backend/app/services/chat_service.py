import json
from typing import AsyncIterator, Optional

from app.domain.models import ContentEvent, DoneEvent, MetadataEvent, ReasoningEvent
from app.domain.rag import format_rag_context, public_sources
from app.domain.schemas import ChatRequest, Settings
from app.infrastructure.db.connection import get_connection
from app.infrastructure.db.repositories import (
    ConversationRepository,
    MessageRepository,
    SettingsRepository,
)
from app.infrastructure.llm.gateway import LLMGateway
from app.services.memory_graph_service import memory_graph_service
from app.services.runtime import (
    FORMAT_SYSTEM_PROMPT,
    MAX_CONTEXT_MESSAGES,
    RAG_SYSTEM_PROMPT,
    rag_service,
)

conversation_repo = ConversationRepository()
message_repo = MessageRepository()
settings_repo = SettingsRepository()
llm_gateway = LLMGateway()


class ChatService:
    """Service handling chat streaming, RAG retrieval, and message persistence via LLMGateway."""

    async def stream_chat(
        self, request: ChatRequest, conversation_id: Optional[int] = None
    ) -> AsyncIterator[str]:
        with get_connection() as conn:
            app_settings = Settings(**settings_repo.get(conn, Settings().model_dump()))

            cid = conversation_id if conversation_id is not None else request.conversation_id
            if cid is None:
                cid = conversation_repo.create(conn)["id"]
            elif not conversation_repo.get(conn, cid):
                raise ValueError("Conversation not found")

            if not request.model:
                raise ValueError("Model must be specified")
            selected_model = request.model

            rag_sources = []
            if request.use_rag and request.document_ids:
                rag_sources = await rag_service.retrieve(request.prompt, request.document_ids, llm_gateway)

            memory_context = ""
            if request.memory_node_ids:
                memory_context = memory_graph_service.compile_context(conn, request.memory_node_ids, depth=1)

            messages = [{"role": "system", "content": FORMAT_SYSTEM_PROMPT}]
            if memory_context:
                messages.append({
                    "role": "system",
                    "content": memory_context,
                })
            if rag_sources:
                messages.append({
                    "role": "system",
                    "content": f"{RAG_SYSTEM_PROMPT}\n\nRetrieved sources:\n{format_rag_context(rag_sources)}",
                })
            messages.extend((request.conversation_history or [])[-MAX_CONTEXT_MESSAGES:])
            messages.append({"role": "user", "content": request.prompt})

            existing_messages = message_repo.list_by_conversation(conn, cid)
            message_repo.add(conn, cid, "user", request.prompt)
            if not existing_messages:
                title = request.prompt[:50] + ("..." if len(request.prompt) > 50 else "")
                conversation_repo.update_title(conn, cid, title)

        accumulated_content = ""
        metadata_event = MetadataEvent(
            model=selected_model,
            conversation_id=cid,
            rag_used=bool(rag_sources),
            sources=public_sources(rag_sources),
            memories_used=request.memory_node_ids or [],
            thinking_enabled=False,
        )
        yield f"data: {metadata_event.model_dump_json()}\n\n"

        async for event in llm_gateway.stream_chat(selected_model, messages):
            if isinstance(event, ReasoningEvent):
                yield f"data: {event.model_dump_json()}\n\n"
            elif isinstance(event, ContentEvent):
                accumulated_content += event.content
                yield f"data: {event.model_dump_json()}\n\n"
            elif isinstance(event, str):
                accumulated_content += event
                content_event = ContentEvent(content=event)
                yield f"data: {content_event.model_dump_json()}\n\n"

        if accumulated_content:
            with get_connection() as conn:
                message_repo.add(
                    conn, cid, "assistant", accumulated_content,
                    selected_model, public_sources(rag_sources),
                )
        done_event = DoneEvent()
        yield f"data: {done_event.model_dump_json()}\n\n"
