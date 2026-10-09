import json
from pathlib import Path

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

def calculate_fit_score(model_vram: float, available_ram: float) -> str:
    """Returns FIT, TIGHT, or UNSUPPORTED based on VRAM requirement vs available RAM."""
    if model_vram <= 0:
        return "FIT"  # Cloud models
    if available_ram >= model_vram * 1.2:
        return "FIT"
    if available_ram >= model_vram:
        return "TIGHT"
    return "UNSUPPORTED"

async def list_models():
    """Returns models currently installed in Ollama."""
    try:
        return {"models": await llm_gateway.get_models("ollama")}
    except Exception as exc:
        logger.error("list_models_failed", error=str(exc))
        return {"models": []}

async def get_catalog():
    """Returns the curated model catalog with calculated fit scores."""
    try:
        with open(CATALOG_PATH, "r") as f:
            catalog = json.load(f)

        resources = hardware_service.get_available_resources()
        available_ram = resources["ram_gb"]

        catalog = [
            model for model in catalog
            if model.get("provider") == "ollama"
        ]

        for model in catalog:
            min_vram = model.get("min_vram_gb", 0)
            model["fit_score"] = calculate_fit_score(min_vram, available_ram)

        return {"catalog": catalog}
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
