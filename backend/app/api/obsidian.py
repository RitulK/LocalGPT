from fastapi import APIRouter, HTTPException
import httpx

from app.domain.schemas import (
    ObsidianActionRequest,
    ObsidianConnectionTestRequest,
    ObsidianProposalRequest,
    ObsidianSearchRequest,
)
from app.domain.models import ContentEvent
from app.infrastructure.llm.gateway import LLMGateway
from app.services.obsidian_service import (
    MASKED_KEY,
    ObsidianService,
    get_saved_settings,
    normalize_vault_path,
    validate_write_path,
)

router = APIRouter(prefix="/obsidian", tags=["obsidian"])
llm_gateway = LLMGateway()
import re


def _slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-Za-z0-9]+", "-", title).strip("-").lower()
    return slug or "Untitled"


async def _generate_text(model: str, messages: list[dict]) -> str:
    accumulated = ""
    async for event in llm_gateway.stream_chat(model, messages, enable_tools=False):
        if isinstance(event, ContentEvent):
            accumulated += event.content
    return accumulated


def _parse_json_object(text: str) -> dict:
    import json
    candidate = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(candidate[start:end + 1])
            except json.JSONDecodeError:
                pass
    raise ValueError("The model did not return a valid Markdown proposal.")


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


@router.get("/notes/{path:path}")
async def read_note(path: str):
    try:
        return await ObsidianService().read(path)
    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/generate-proposal")
async def generate_proposal(request: ObsidianProposalRequest):
    if not request.model:
        raise HTTPException(status_code=400, detail="A chat model is required.")

    saved = get_saved_settings()
    allowed_folder = str(saved.get("obsidian_allowed_folder", "BuddyAI/")).strip("/")
    tool = request.tool
    action_map = {
        "new_note": "create",
        "append": "append",
        "edit": "edit",
        "replace": "replace",
        "delete": "delete",
    }
    action = action_map[tool]
    target_path = normalize_vault_path(request.target_path) if request.target_path else None

    if action in {"append", "edit", "replace", "delete"}:
        if not target_path:
            raise HTTPException(status_code=400, detail="A target note path is required.")
        try:
            target_path = validate_write_path(target_path, saved.get("obsidian_allowed_folder", ""))
            note = await ObsidianService().read(target_path)
        except (ValueError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    else:
        note = None

    system = (
        "You are an Obsidian Markdown writing assistant. Return only one JSON object. "
        "Do not execute tools or include markdown fences. The JSON must use these keys: "
        "action, path, content, section, title, reason. "
        "Use action=" + action + ". "
        "Use a vault-relative Markdown path and keep it inside the allowed folder. "
        "For create actions, derive a descriptive .md path unless an explicit title is clear. "
        "For edit actions, section is optional and should identify a heading only when known."
    )
    context = (request.conversation_history or [])[-6:]
    user_context = [
        {"role": "system", "content": system},
        *context,
        {"role": "system", "content": f"Allowed write folder: {allowed_folder or '(vault root)' }"},
    ]
    if target_path:
        user_context.append({
            "role": "system",
            "content": f"Target note path: {target_path}\nTarget section: {request.section or ''}",
        })
    if note:
        user_context.append({
            "role": "system",
            "content": f"Current target note content:\n\n{note['content']}",
        })
    user_context.append({
        "role": "user",
        "content": request.prompt,
    })

    try:
        generated = await _generate_text(request.model, user_context)
        proposal = _parse_json_object(generated)
    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if action == "create":
        title = str(proposal.get("title") or "Untitled").strip()
        proposed_path = str(proposal.get("path") or f"{allowed_folder}/{title}.md" if allowed_folder else f"{title}.md").strip("/")
        if not proposed_path.lower().endswith(".md"):
            proposed_path += ".md"
        if "/" not in proposed_path and allowed_folder:
            proposed_path = f"{allowed_folder}/{proposed_path}"
        proposal["path"] = proposed_path
    elif target_path:
        proposal["path"] = target_path

    proposal["action"] = action
    if action in {"edit", "append"} and request.section:
        proposal["section"] = request.section
    if note:
        proposal["if_match"] = note["if_match"]

    try:
        proposal["path"] = validate_write_path(str(proposal["path"]), saved.get("obsidian_allowed_folder", ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if action in {"append", "edit", "replace"} and not proposal.get("content"):
        raise HTTPException(status_code=400, detail="The model did not generate note content.")

    return {"proposal": proposal}


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


@router.post("/proposals/confirm")
async def confirm_proposal(action_request: ObsidianActionRequest):
    return await execute(action_request)


@router.post("/proposals/cancel")
async def cancel_proposal():
    return {"cancelled": True}
