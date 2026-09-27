import json
from typing import AsyncIterator, Optional

import database
from app.domain.rag import format_rag_context, public_sources
from app.domain.schemas import ChatRequest, Settings
from app.services.runtime import (
    FORMAT_SYSTEM_PROMPT,
    MAX_CONTEXT_MESSAGES,
    RAG_SYSTEM_PROMPT,
    model_router,
    nvidia_client,
    ollama_client,
    rag_service,
    vllm_client,
)


class ChatService:
    """Service handling chat streaming, routing, RAG retrieval, and message persistence."""

    async def stream_chat(
        self, request: ChatRequest, conversation_id: Optional[int] = None
    ) -> AsyncIterator[str]:
        app_settings = Settings(**database.get_settings(Settings().dict()))

        cid = conversation_id if conversation_id is not None else request.conversation_id
        if cid is None:
            cid = database.create_conversation()["id"]
        elif not database.get_conversation(cid):
            raise ValueError("Conversation not found")

        if request.use_router:
            selected_model = model_router.route(prompt=request.prompt, settings=app_settings)
        elif request.model:
            selected_model = request.model
        else:
            raise ValueError("Model must be specified when router is disabled")

        rag_sources = []
        if request.use_rag and request.document_ids:
            rag_sources = await rag_service.retrieve(request.prompt, request.document_ids, ollama_client)

        messages = [{"role": "system", "content": FORMAT_SYSTEM_PROMPT}]
        if rag_sources:
            messages.append({
                "role": "system",
                "content": f"{RAG_SYSTEM_PROMPT}\n\nRetrieved sources:\n{format_rag_context(rag_sources)}",
            })
        messages.extend((request.conversation_history or [])[-MAX_CONTEXT_MESSAGES:])
        messages.append({"role": "user", "content": request.prompt})

        existing_messages = database.list_messages(cid)
        database.add_message(cid, "user", request.prompt)
        if not existing_messages:
            title = request.prompt[:50] + ("..." if len(request.prompt) > 50 else "")
            database.update_conversation_title(cid, title)

        is_nvidia_model = "nvidia/" in selected_model.lower() or "nemotron" in selected_model.lower()
        is_vllm_model = selected_model.lower().startswith("llama-3.3-nemotron") and not is_nvidia_model
        selected_client = nvidia_client if is_nvidia_model else (vllm_client if is_vllm_model else ollama_client)
        enable_thinking = request.enable_thinking or app_settings.enable_thinking if is_nvidia_model else False
        reasoning_budget = request.reasoning_budget or app_settings.reasoning_budget if is_nvidia_model else 0

        accumulated_content = ""
        metadata = {
            "type": "metadata",
            "model": selected_model,
            "routing_used": request.use_router,
            "conversation_id": cid,
            "rag_used": bool(rag_sources),
            "sources": public_sources(rag_sources),
            "thinking_enabled": enable_thinking if is_nvidia_model else False,
        }
        yield f"data: {json.dumps(metadata)}\n\n"

        if is_nvidia_model and nvidia_client:
            stream = nvidia_client.chat_stream(
                selected_model, messages, enable_thinking=enable_thinking,
                reasoning_budget=reasoning_budget,
            )
        else:
            stream = selected_client.chat_stream(selected_model, messages)

        async for chunk in stream:
            if not chunk:
                continue
            if is_nvidia_model and "[REASONING]" in chunk:
                for part in chunk.split("[REASONING]"):
                    if "[/REASONING]" in part:
                        reasoning_part, rest = part.split("[/REASONING]", 1)
                        try:
                            reasoning_data = json.loads(reasoning_part)
                        except json.JSONDecodeError:
                            reasoning_data = None
                        if reasoning_data:
                            yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_data.get('content', '')})}\n\n"
                        if rest:
                            accumulated_content += rest
                    else:
                        accumulated_content += part
                continue
            accumulated_content += chunk
            yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

        if accumulated_content:
            database.add_message(
                cid, "assistant", accumulated_content,
                selected_model, public_sources(rag_sources),
            )
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
