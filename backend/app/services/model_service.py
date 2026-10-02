from app.services.runtime import llm_gateway


async def list_models():
    models = []
    for provider in ("ollama", "vllm", "nvidia"):
        try:
            models.extend(await llm_gateway.get_models(provider))
        except Exception as exc:
            print(f"Warning: Could not fetch {provider} models: {exc}")
    return {"models": models}
