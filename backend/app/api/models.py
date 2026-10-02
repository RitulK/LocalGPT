from fastapi import APIRouter

from app.services import model_service

router = APIRouter()


@router.get("/models")
async def get_models():
    return await model_service.list_models()
