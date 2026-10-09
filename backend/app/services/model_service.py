from app.services.runtime import llm_gateway
from app.core.logging import logger


async def list_models():
    models = []
    for provider in ("ollama", "vllm", "nvidia"):
        try:
            models.extend(await llm_gateway.get_models(provider))
        except Exception as exc:
            logger.warning("could_not_fetch_models", provider=provider, error=str(exc))
    return {"models": models}
