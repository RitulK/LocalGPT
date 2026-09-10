import database

from app.services.runtime import default_settings


def get_settings():
    return database.get_settings(default_settings())


def update_settings(settings: dict):
    saved_settings = database.save_settings(settings)
    return {"message": "Settings updated", "settings": saved_settings}
