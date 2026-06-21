from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import json
from pathlib import Path

import database
from ollama_client import OllamaClient
from vllm_client import VLLMClient
from nvidia_client import NvidiaClient
from rag_service import RAGService
from router import ModelRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    database.init_db()
    rag_service.ensure_storage()
    yield
    # Shutdown event (if needed)


app = FastAPI(title="LocalGPT API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
ollama_client = OllamaClient()
vllm_client = VLLMClient()

# Initialize Nvidia client (optional - requires API key)
nvidia_client = None
try:
    nvidia_client = NvidiaClient()
except ValueError as e:
    print(f"Warning: Nvidia client not available - {str(e)}")

model_router = ModelRouter()
rag_service = RAGService()

MAX_CONTEXT_MESSAGES = 6
FORMAT_SYSTEM_PROMPT = (
    "Format answers in clean Markdown. When the user asks for a table, output a "
    "valid GitHub-Flavored Markdown table with each row on its own line, a header "
    "separator row, and no table inside a code block."
)
RAG_SYSTEM_PROMPT = (
    "You are answering with a user-selected local knowledge base. Use the retrieved "
    "sources below as the primary ground truth. Cite relevant sources with bracketed "
    "numbers like [1]. If the sources do not contain enough information, say that "
    "the uploaded documents do not provide enough detail and then clearly separate "
    "any general knowledge."
)


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    use_router: bool = False
    conversation_id: Optional[int] = None
    conversation_history: Optional[List[dict]] = None
    use_rag: bool = False
    document_ids: Optional[List[int]] = None
    enable_thinking: bool = False  # For Nvidia Nemotron reasoning
    reasoning_budget: int = 8192  # Max tokens for thinking


class Settings(BaseModel):
    default_general_model: Optional[str] = None
    default_coding_model: Optional[str] = None
    default_reasoning_model: Optional[str] = None
    router_enabled: bool = True
    router_models: Optional[List[str]] = None
    enable_thinking: bool = False  # Enable reasoning for Nvidia models
    reasoning_budget: int = 8192


def default_settings() -> dict:
    return Settings().dict()


class ConversationCreate(BaseModel):
    title: str = "New Chat"


class MemoryCreate(BaseModel):
    kind: str = "note"
    content: str
    source: Optional[str] = None


def public_sources(sources: List[dict]) -> List[dict]:
    return [
        {
            "source_index": source["source_index"],
            "document_id": source["document_id"],
            "filename": source["filename"],
            "chunk_index": source["chunk_index"],
            "page_number": source["page_number"],
            "distance": source["distance"],
            "snippet": source["snippet"],
        }
        for source in sources
    ]


def format_rag_context(sources: List[dict]) -> str:
    context_blocks = []
    for source in sources:
        page = f", page {source['page_number']}" if source.get("page_number") else ""
        context_blocks.append(
            f"[{source['source_index']}] {source['filename']}{page}\n"
            f"{source['content']}"
        )
    return "\n\n".join(context_blocks)


@app.get("/")
async def root():
    return {"message": "LocalGPT API - Running", "status": "online"}


@app.get("/health")
async def health_check():
    """Check if Ollama is running"""
    try:
        models = await ollama_client.get_models()
        return {
            "status": "healthy",
            "ollama_running": True,
            "models_available": len(models)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "ollama_running": False,
            "error": str(e)
        }


@app.get("/models")
async def get_models():
    """Get all installed models from Ollama, vLLM, and Nvidia"""
    try:
        ollama_models = []
        vllm_models = []
        nvidia_models = []
        
        try:
            ollama_models = await ollama_client.get_models()
        except Exception as e:
            print(f"Warning: Could not fetch Ollama models: {str(e)}")
        
        try:
            vllm_models = await vllm_client.get_models()
        except Exception as e:
            print(f"Warning: Could not fetch vLLM models: {str(e)}")
        
        try:
            if nvidia_client:
                nvidia_models = await nvidia_client.get_models()
        except Exception as e:
            print(f"Warning: Could not fetch Nvidia models: {str(e)}")
        
        all_models = ollama_models + vllm_models + nvidia_models
        return {"models": all_models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")


@app.get("/conversations")
async def list_conversations():
    """List saved conversations with their messages"""
    conversations = database.list_conversations()
    for conversation in conversations:
        conversation["messages"] = database.list_messages(conversation["id"])
    return {"conversations": conversations}


@app.post("/conversations")
async def create_conversation(request: ConversationCreate):
    """Create a new conversation"""
    conversation = database.create_conversation(request.title)
    conversation["messages"] = []
    return {"conversation": conversation}


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int):
    """Get one conversation with its messages"""
    conversation = database.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation["messages"] = database.list_messages(conversation_id)
    return {"conversation": conversation}


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete a conversation and all of its messages"""
    deleted = database.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted"}


@app.delete("/conversations/{conversation_id}/messages")
async def clear_conversation(conversation_id: int):
    """Clear messages from a conversation"""
    if not database.get_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    database.clear_messages(conversation_id)
    return {"message": "Conversation cleared"}


@app.get("/documents")
async def list_documents():
    """List uploaded knowledge-base documents"""
    return {"documents": database.list_documents()}


@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a PDF or TXT document for RAG"""
    try:
        document = await rag_service.ingest_upload(file, ollama_client)
        return {"document": document}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")


@app.get("/documents/{document_id}")
async def get_document(document_id: int):
    """Get one knowledge-base document"""
    document = database.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"document": document}


@app.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """Delete a document, its stored file, metadata, and vectors"""
    document = database.delete_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    rag_service.delete_document_vectors(document_id)
    try:
        Path(document["file_path"]).unlink(missing_ok=True)
    except OSError:
        pass

    return {"message": "Document deleted"}


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with streaming support
    - If use_router is True, automatically select the best model
    - Otherwise use the specified model
    """
    try:
        app_settings = Settings(**database.get_settings(default_settings()))

        conversation_id = request.conversation_id
        if conversation_id is None:
            conversation = database.create_conversation()
            conversation_id = conversation["id"]
        elif not database.get_conversation(conversation_id):
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Determine which model to use
        if request.use_router:
            selected_model = model_router.route(
                prompt=request.prompt,
                settings=app_settings
            )
        else:
            if not request.model:
                raise HTTPException(status_code=400, detail="Model must be specified when router is disabled")
            selected_model = request.model
        
        rag_sources = []
        if request.use_rag and request.document_ids:
            rag_sources = await rag_service.retrieve(
                request.prompt,
                request.document_ids,
                ollama_client,
            )

        # Keep only recent context so prompt processing does not grow forever.
        messages = [{"role": "system", "content": FORMAT_SYSTEM_PROMPT}]
        if rag_sources:
            messages.append(
                {
                    "role": "system",
                    "content": f"{RAG_SYSTEM_PROMPT}\n\nRetrieved sources:\n{format_rag_context(rag_sources)}",
                }
            )
        messages.extend((request.conversation_history or [])[-MAX_CONTEXT_MESSAGES:])
        messages.append({"role": "user", "content": request.prompt})

        existing_messages = database.list_messages(conversation_id)
        database.add_message(conversation_id, "user", request.prompt)
        if not existing_messages:
            title = request.prompt[:50] + ("..." if len(request.prompt) > 50 else "")
            database.update_conversation_title(conversation_id, title)
        
        # Determine which client to use based on model provider
        is_nvidia_model = "nvidia/" in selected_model.lower() or "nemotron" in selected_model.lower()
        is_vllm_model = selected_model.lower().startswith("llama-3.3-nemotron") and not is_nvidia_model
        
        if is_nvidia_model:
            selected_client = nvidia_client
            # Merge settings and request reasoning preferences for Nvidia
            enable_thinking = request.enable_thinking or app_settings.enable_thinking
            reasoning_budget = request.reasoning_budget or app_settings.reasoning_budget
        else:
            selected_client = vllm_client if is_vllm_model else ollama_client
            enable_thinking = False
            reasoning_budget = 0
        
        # Stream response from appropriate provider
        async def generate():
            accumulated_content = ""
            accumulated_reasoning = ""

            # Send metadata first
            metadata = {
                "type": "metadata",
                "model": selected_model,
                "routing_used": request.use_router,
                "conversation_id": conversation_id,
                "rag_used": bool(rag_sources),
                "sources": public_sources(rag_sources),
                "thinking_enabled": enable_thinking if is_nvidia_model else False,
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Stream the actual response from appropriate client
            if is_nvidia_model and nvidia_client:
                async for chunk in nvidia_client.chat_stream(
                    selected_model, 
                    messages,
                    enable_thinking=enable_thinking,
                    reasoning_budget=reasoning_budget
                ):
                    if chunk:
                        # Check if this is reasoning content
                        if "[REASONING]" in chunk:
                            # Extract and yield reasoning separately
                            parts = chunk.split("[REASONING]")
                            for i, part in enumerate(parts):
                                if "[/REASONING]" in part:
                                    reasoning_part, rest = part.split("[/REASONING]", 1)
                                    if reasoning_part:
                                        try:
                                            reasoning_data = json.loads(reasoning_part)
                                            accumulated_reasoning += reasoning_data.get("content", "")
                                            # Optionally yield reasoning
                                            data = {
                                                "type": "reasoning",
                                                "content": reasoning_data.get("content", "")
                                            }
                                            yield f"data: {json.dumps(data)}\n\n"
                                        except json.JSONDecodeError:
                                            pass
                                    if rest:
                                        accumulated_content += rest
                                else:
                                    accumulated_content += part
                            continue
                        
                        accumulated_content += chunk
                        data = {
                            "type": "content",
                            "content": chunk
                        }
                        yield f"data: {json.dumps(data)}\n\n"
            else:
                async for chunk in selected_client.chat_stream(selected_model, messages):
                    if chunk:
                        accumulated_content += chunk
                        data = {
                            "type": "content",
                            "content": chunk
                        }
                        yield f"data: {json.dumps(data)}\n\n"
            
            if accumulated_content:
                database.add_message(
                    conversation_id,
                    "assistant",
                    accumulated_content,
                    selected_model,
                    public_sources(rag_sources),
                )

            # Send completion signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/settings")
async def get_settings():
    """Get current settings"""
    return database.get_settings(default_settings())


@app.post("/settings")
async def update_settings(settings: Settings):
    """Update settings"""
    saved_settings = database.save_settings(settings.dict())
    return {"message": "Settings updated", "settings": saved_settings}


@app.get("/memories")
async def list_memories():
    """List saved long-term memories"""
    return {"memories": database.list_memories()}


@app.post("/memories")
async def create_memory(request: MemoryCreate):
    """Create a long-term memory note"""
    memory = database.create_memory(request.kind, request.content, request.source)
    return {"memory": memory}


@app.delete("/memories/{memory_id}")
async def delete_memory(memory_id: int):
    """Delete a long-term memory note"""
    deleted = database.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory deleted"}


@app.post("/router/test")
async def test_router(request: ChatRequest):
    """Test which model the router would select without actually running inference"""
    app_settings = Settings(**database.get_settings(default_settings()))
    selected_model = model_router.route(
        prompt=request.prompt,
        settings=app_settings
    )
    reasoning = model_router.get_routing_reasoning(request.prompt, app_settings)
    
    return {
        "selected_model": selected_model,
        "reasoning": reasoning,
        "prompt": request.prompt
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
