from fastapi import APIRouter, HTTPException, Request

from app.domain.schemas import Settings
from app.services import settings_service
from app.core.local_access import require_local_request

router = APIRouter()
OBSIDIAN_SETTING_KEYS = {
    "obsidian_api_address",
    "obsidian_api_key",
    "obsidian_verify_tls",
    "obsidian_ca_path",
    "obsidian_allowed_folder",
    "obsidian_display_name",
    "obsidian_allow_read",
    "obsidian_allow_write",
    "obsidian_allow_delete",
}


@router.get("/settings")
async def get_settings():
    return settings_service.get_settings()


@router.post("/settings")
async def update_settings(settings: Settings, request: Request):
    values = settings.model_dump()
    existing = settings_service.get_settings()
    if any(values[key] != existing.get(key) for key in OBSIDIAN_SETTING_KEYS):
        try:
            await require_local_request(request)
        except HTTPException as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail="Obsidian settings can only be changed by a local client.",
            ) from exc
    return settings_service.update_settings(values)
