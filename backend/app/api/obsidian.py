from fastapi import APIRouter, HTTPException
import httpx

from app.domain.schemas import (
    ObsidianActionRequest,
    ObsidianConnectionTestRequest,
    ObsidianSearchRequest,
)
from app.services.obsidian_service import (
    MASKED_KEY,
    ObsidianService,
    get_saved_settings,
    normalize_vault_path,
    validate_write_path,
)

router = APIRouter(prefix="/obsidian", tags=["obsidian"])


@router.get("/status")
async def status():
    service = ObsidianService()
    try:
        return await service.test_connection()
    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/test")
async def test_connection(request: ObsidianConnectionTestRequest):
    saved = get_saved_settings()
    api_key = request.api_key
    if api_key == MASKED_KEY:
        api_key = None
    config = {
        "obsidian_api_address": request.api_address or saved["obsidian_api_address"],
        "obsidian_api_key": api_key or saved["obsidian_api_key"],
        "obsidian_verify_tls": request.verify_tls,
        "obsidian_ca_path": request.ca_path,
        "obsidian_display_name": saved.get("obsidian_display_name", ""),
    }
    try:
        return await ObsidianService(config).test_connection()
    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/search")
async def search(request: ObsidianSearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="A search query is required.")
    try:
        return await ObsidianService().search(request.query.strip(), request.max_results)
    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/plan")
async def plan(action_request: ObsidianActionRequest):
    action = action_request.model_dump(exclude_none=True)
    kind = action["action"]
    if kind in {"search", "open"}:
        if kind == "search" and not action.get("query", "").strip():
            raise HTTPException(status_code=400, detail="A search query is required.")
        if kind == "open" and not action.get("path"):
            raise HTTPException(status_code=400, detail="A note path is required.")
    else:
        if not action.get("path"):
            raise HTTPException(status_code=400, detail="A note path is required.")
        if kind != "delete" and action.get("content") is None:
            raise HTTPException(status_code=400, detail="Note content is required.")

    saved = get_saved_settings()
    if kind not in {"search", "open"}:
        try:
            action["path"] = validate_write_path(action["path"], saved.get("obsidian_allowed_folder", ""))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    elif kind == "open":
        try:
            action["path"] = normalize_vault_path(action["path"])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    if kind in {"append", "edit", "replace", "delete"}:
        try:
            note = await ObsidianService().read(action["path"])
            action["if_match"] = note["if_match"]
        except (ValueError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return {"proposal": action, "requires_confirmation": kind in {"create", "append", "edit", "replace", "delete"}}


@router.post("/execute")
async def execute(action_request: ObsidianActionRequest):
    action = action_request.model_dump(exclude_none=True)
    try:
        return await ObsidianService().execute(action)
    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
