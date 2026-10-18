from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

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


@router.post("/models/install-stream/{model_id}")
async def install_model_stream(model_id: str):
    async def events():
        async for update in model_service.stream_install_model(model_id):
            yield f"data: {json.dumps(update)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
