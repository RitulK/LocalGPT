from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json

import database
from ollama_client import OllamaClient
from router import ModelRouter

app = FastAPI(title="LocalGPT API")

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
model_router = ModelRouter()

MAX_CONTEXT_MESSAGES = 6
FORMAT_SYSTEM_PROMPT = (
    "Format answers in clean Markdown. When the user asks for a table, output a "
    "valid GitHub-Flavored Markdown table with each row on its own line, a header "
    "separator row, and no table inside a code block."
)


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    use_router: bool = False
    conversation_id: Optional[int] = None
    conversation_history: Optional[List[dict]] = None


class Settings(BaseModel):
    default_general_model: Optional[str] = None
    default_coding_model: Optional[str] = None
    default_reasoning_model: Optional[str] = None
    router_enabled: bool = True


class ConversationCreate(BaseModel):
    title: str = "New Chat"


class MemoryCreate(BaseModel):
    kind: str = "note"
    content: str
    source: Optional[str] = None


def default_settings() -> dict:
    return Settings().dict()


@app.on_event("startup")
async def startup():
    database.init_db()


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
    """Get all installed Ollama models"""
    try:
        models = await ollama_client.get_models()
        return {"models": models}
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
        
        # Keep only recent context so prompt processing does not grow forever.
        messages = [{"role": "system", "content": FORMAT_SYSTEM_PROMPT}]
        messages.extend((request.conversation_history or [])[-MAX_CONTEXT_MESSAGES:])
        messages.append({"role": "user", "content": request.prompt})

        existing_messages = database.list_messages(conversation_id)
        database.add_message(conversation_id, "user", request.prompt)
        if not existing_messages:
            title = request.prompt[:50] + ("..." if len(request.prompt) > 50 else "")
            database.update_conversation_title(conversation_id, title)
        
        # Stream response from Ollama
        async def generate():
            accumulated_content = ""

            # Send metadata first
            metadata = {
                "type": "metadata",
                "model": selected_model,
                "routing_used": request.use_router,
                "conversation_id": conversation_id
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Stream the actual response
            async for chunk in ollama_client.chat_stream(selected_model, messages):
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
