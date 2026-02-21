from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import asyncio

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


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    use_router: bool = False
    conversation_history: Optional[List[dict]] = None


class Settings(BaseModel):
    default_general_model: Optional[str] = None
    default_coding_model: Optional[str] = None
    default_reasoning_model: Optional[str] = None
    router_enabled: bool = True


# Store settings in memory (in production, use a database)
app_settings = Settings()


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


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with streaming support
    - If use_router is True, automatically select the best model
    - Otherwise use the specified model
    """
    try:
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
        
        # Prepare messages
        messages = request.conversation_history or []
        messages.append({"role": "user", "content": request.prompt})
        
        # Stream response from Ollama
        async def generate():
            # Send metadata first
            metadata = {
                "type": "metadata",
                "model": selected_model,
                "routing_used": request.use_router
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Stream the actual response
            async for chunk in ollama_client.chat_stream(selected_model, messages):
                if chunk:
                    data = {
                        "type": "content",
                        "content": chunk
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            
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
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/settings")
async def get_settings():
    """Get current settings"""
    return app_settings.dict()


@app.post("/settings")
async def update_settings(settings: Settings):
    """Update settings"""
    global app_settings
    app_settings = settings
    return {"message": "Settings updated", "settings": app_settings.dict()}


@app.post("/router/test")
async def test_router(request: ChatRequest):
    """Test which model the router would select without actually running inference"""
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
