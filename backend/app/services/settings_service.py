from app.infrastructure.db.connection import get_connection
from app.infrastructure.db.repositories import SettingsRepository
from app.services.runtime import default_settings
from app.services.obsidian_service import public_settings, update_saved_settings

settings_repo = SettingsRepository()


def get_settings():
    return public_settings()


def update_settings(settings: dict):
    saved_settings = update_saved_settings(settings)
    return {"message": "Settings updated", "settings": saved_settings}
