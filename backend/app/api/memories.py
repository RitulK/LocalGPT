from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.domain.schemas import (
    MemoryCreate,
    MemoryEdgeCreate,
    MessageCaptureRequest,
    ThreadCaptureRequest,
)
from app.services import memory_service
from app.services.memory_graph_service import memory_graph_service

router = APIRouter()


@router.get("/memories")
async def list_memories():
    return memory_service.list_memories()


@router.post("/memories")
async def create_memory(request: MemoryCreate):
    return memory_service.create_memory(request.kind, request.content, request.source)


@router.get("/memories/graph")
async def get_memory_graph(
    node_type: Optional[str] = Query(None),
    conversation_id: Optional[int] = Query(None),
):
    return memory_graph_service.get_graph(node_type=node_type, conversation_id=conversation_id)


@router.post("/memories/capture/message")
async def capture_message(request: MessageCaptureRequest):
    try:
        node = memory_graph_service.capture_message(
            conversation_id=request.conversation_id,
            message_id=request.message_id,
            title=request.title,
        )
        return {"node": node, "status": "captured"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/memories/capture/thread")
async def capture_thread(request: ThreadCaptureRequest):
    try:
        result = memory_graph_service.capture_thread(
            conversation_id=request.conversation_id,
            up_to_message_id=request.up_to_message_id,
            title=request.title,
        )
        return {**result, "status": "captured"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/memories/edges")
async def create_edge(request: MemoryEdgeCreate):
    try:
        edge = memory_graph_service.create_edge(
            source_id=request.source_id,
            target_id=request.target_id,
            relation=request.relation,
            metadata=request.metadata,
        )
        return {"edge": edge, "status": "created"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/memories/edges/{edge_id}")
async def delete_edge(edge_id: int):
    if not memory_graph_service.delete_edge(edge_id):
        raise HTTPException(status_code=404, detail="Edge not found")
    return {"message": "Edge deleted"}


@router.delete("/memories/{memory_id}")
async def delete_memory(memory_id: str):
    # Try deleting graph memory node first
    deleted = memory_graph_service.delete_node(memory_id)
    if not deleted and memory_id.isdigit():
        deleted = memory_service.delete_memory(int(memory_id))

    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory deleted"}
