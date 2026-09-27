from app.domain.schemas import Settings
from app.infrastructure.db.connection import get_connection
from app.infrastructure.db.repositories import SettingsRepository
from app.services.runtime import default_settings, llm_gateway, model_router

settings_repo = SettingsRepository()


async def list_models():
    models = []
    for provider in ("ollama", "vllm", "nvidia"):
        try:
            models.extend(await llm_gateway.get_models(provider))
        except Exception as exc:
            print(f"Warning: Could not fetch {provider} models: {exc}")
    return {"models": models}


def test_route(prompt: str, settings):
    selected_model = model_router.route(prompt=prompt, settings=settings)
    return {
        "selected_model": selected_model,
        "reasoning": model_router.get_routing_reasoning(prompt, settings),
        "prompt": prompt,
    }


def test_route_request(prompt: str):
    with get_connection() as conn:
        settings = Settings(**settings_repo.get(conn, default_settings()))
    return test_route(prompt, settings)
