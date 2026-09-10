from fastapi import APIRouter, HTTPException

from app.domain.schemas import MemoryCreate
from app.services import memory_service

router = APIRouter()


@router.get("/memories")
async def list_memories():
    return memory_service.list_memories()


@router.post("/memories")
async def create_memory(request: MemoryCreate):
    return memory_service.create_memory(request.kind, request.content, request.source)


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: int):
    if not memory_service.delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory deleted"}
