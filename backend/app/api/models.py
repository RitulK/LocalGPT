from fastapi import APIRouter

from app.domain.schemas import ChatRequest
from app.services import model_service

router = APIRouter()


@router.get("/models")
async def get_models():
    return await model_service.list_models()


@router.post("/router/test")
async def test_router(request: ChatRequest):
    return model_service.test_route_request(request.prompt)
