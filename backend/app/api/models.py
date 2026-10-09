from fastapi import APIRouter, HTTPException

from app.services import model_service

router = APIRouter()


@router.get("/models")
async def get_models():
    return await model_service.list_models()


@router.get("/models/catalog")
async def get_catalog():
    return await model_service.get_catalog()


@router.post("/models/install/{model_id}")
async def install_model(model_id: str):
    result = await model_service.install_model(model_id)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
