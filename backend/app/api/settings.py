from fastapi import APIRouter

from app.domain.schemas import Settings
from app.services import settings_service

router = APIRouter()


@router.get("/settings")
async def get_settings():
    return settings_service.get_settings()


@router.post("/settings")
async def update_settings(settings: Settings):
    return settings_service.update_settings(settings.dict())
