from fastapi import APIRouter

from app.services.runtime import ollama_client, rag_service

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "LocalGPT API - Running", "status": "online"}


@router.get("/health")
async def health_check():
    try:
        models = await ollama_client.get_models()
        return {"status": "healthy", "ollama_running": True, "models_available": len(models)}
    except Exception as exc:
        return {"status": "unhealthy", "ollama_running": False, "error": str(exc)}
