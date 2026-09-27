from app.infrastructure.db.connection import get_connection
from app.infrastructure.db.repositories import SettingsRepository
from app.services.runtime import default_settings

settings_repo = SettingsRepository()


def get_settings():
    with get_connection() as conn:
        return settings_repo.get(conn, default_settings())


def update_settings(settings: dict):
    with get_connection() as conn:
        saved_settings = settings_repo.save(conn, settings)
        return {"message": "Settings updated", "settings": saved_settings}
