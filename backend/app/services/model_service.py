import json
from pathlib import Path
from typing import Any, Dict

import httpx

from app.services.runtime import llm_gateway
from app.services.hardware_service import hardware_service
from app.core.logging import logger

CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "infrastructure"
    / "llm"
    / "catalog.json"
)

def calculate_fit_score(required_gb: float, available_ram: float) -> Dict[str, Any]:
    """Estimate local compatibility from the model size and available system memory."""
    if required_gb <= 0:
        return {"score": 100, "label": "Cloud", "status": "FIT"}

    ratio = min(available_ram / required_gb, 1.0)
    score = round(ratio * 100)
    if available_ram >= required_gb * 1.2:
        status = "FIT"
    elif available_ram >= required_gb:
        status = "TIGHT"
    else:
        status = "UNSUPPORTED"
    return {"score": score, "label": status, "status": status}

async def list_models():
    """Returns models currently installed in Ollama."""
    try:
        return {"models": await llm_gateway.get_models("ollama")}
    except Exception as exc:
        logger.error("list_models_failed", error=str(exc))
        return {"models": []}

async def get_catalog():
    """Return Ollama's catalogue enriched with local install and compatibility data."""
    try:
        with open(CATALOG_PATH, "r") as f:
            curated = json.load(f)

        resources = hardware_service.get_available_resources()
        available_ram = resources["ram_gb"]
        live_models = await llm_gateway.get_models("ollama")
        catalog_by_id = {
            model["id"]: dict(model)
            for model in curated
            if model.get("provider") == "ollama"
        }

        # Ollama exposes the public catalogue through the same tags shape as its
        # local API. Keep the bundled entries as a fallback when it is offline.
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                response = await client.get("https://ollama.com/api/tags")
                response.raise_for_status()
                for public_model in response.json().get("models", []):
                    model_id = public_model.get("name")
                    if model_id:
                        catalog_by_id.setdefault(model_id, {
                            "id": model_id,
                            "name": model_id,
                            "description": "Available from the Ollama model catalogue.",
                            "provider": "ollama",
                            "size": public_model.get("size", 0),
                            "details": public_model.get("details", {}),
                        })
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("ollama_catalog_unavailable", error=str(exc))

        for live_model in live_models:
            model_id = live_model["name"].removeprefix("ollama:")
            entry = catalog_by_id.setdefault(model_id, {
                "id": model_id,
                "name": model_id,
                "description": "Model available from this Ollama instance.",
                "provider": "ollama",
            })
            size_gb = (live_model.get("size") or 0) / (1024 ** 3)
            entry["installed"] = True
            entry["size"] = live_model.get("size", 0)
            entry["modified_at"] = live_model.get("modified_at")
            entry["details"] = live_model.get("details", {})
            entry["required_memory_gb"] = round(size_gb, 2)

        for model in catalog_by_id.values():
            required_memory = model.get("required_memory_gb") or model.get("min_vram_gb", 0)
            if ":cloud" in model["id"] or model.get("size") == 0:
                required_memory = 0
            fit = calculate_fit_score(required_memory, available_ram)
            model["fit_score"] = fit["score"]
            model["fit_label"] = fit["label"]
            model["fit_status"] = fit["status"]
            model["available_ram_gb"] = available_ram

        return {"catalog": list(catalog_by_id.values()), "hardware": resources}
    except Exception as exc:
        logger.error("get_catalog_failed", error=str(exc))
        return {"catalog": [], "error": str(exc)}

async def install_model(model_id: str):
    """Triggers installation of a model from the catalog."""
    logger.info("installing_model", model_id=model_id)
    result = await llm_gateway.pull_model(model_id)
    if "error" in result:
        logger.error("install_model_failed", model_id=model_id, error=result["error"])
    else:
        logger.info("install_model_success", model_id=model_id)
    return result
