import json
import re
import secrets
import threading
import time
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.domain.schemas import (
    ObsidianActionRequest,
    ObsidianConnectionTestRequest,
    ObsidianProposalCancellation,
    ObsidianProposalConfirmation,
    ObsidianProposalRequest,
    ObsidianSearchRequest,
)
from app.domain.models import ContentEvent
from app.core.local_access import is_loopback_host, require_local_request
from app.infrastructure.llm.gateway import LLMGateway
from app.services.obsidian_service import (
    MASKED_KEY,
    ObsidianService,
    get_saved_settings,
    normalize_vault_path,
    validate_write_path,
)

_pending_proposals: dict[str, tuple[dict, float]] = {}
_pending_proposals_lock = threading.Lock()
_proposal_lifetime_seconds = 600
_max_pending_proposals = 100


def _validate_test_address(address: str) -> str:
    try:
        parsed = urlsplit(address)
        hostname = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise ValueError("Obsidian API address is invalid.") from exc
    if parsed.scheme not in {"https", "http"} or not hostname:
        raise ValueError("Obsidian API address must be an HTTP(S) URL with a host.")
    if parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("Obsidian API address must contain only the server origin.")
    if not is_loopback_host(hostname):
        raise ValueError("Connection tests may target only a loopback Obsidian API address.")
    return f"{parsed.scheme}://{parsed.netloc}"


def _save_proposal(proposal: dict) -> str:
    now = time.monotonic()
    with _pending_proposals_lock:
        expired = [key for key, (_, deadline) in _pending_proposals.items() if deadline <= now]
        for key in expired:
            _pending_proposals.pop(key, None)
        if len(_pending_proposals) >= _max_pending_proposals:
            raise HTTPException(status_code=429, detail="Too many pending Obsidian proposals.")
        proposal_id = secrets.token_urlsafe(32)
        _pending_proposals[proposal_id] = (proposal.copy(), now + _proposal_lifetime_seconds)
    return proposal_id


def _take_proposal(proposal_id: str) -> dict | None:
    with _pending_proposals_lock:
        pending = _pending_proposals.pop(proposal_id, None)
    if not pending or pending[1] <= time.monotonic():
        return None
    return pending[0]


def _cancel_proposal(proposal_id: str) -> bool:
    with _pending_proposals_lock:
        return _pending_proposals.pop(proposal_id, None) is not None


router = APIRouter(prefix="/obsidian", tags=["obsidian"], dependencies=[Depends(require_local_request)])
llm_gateway = LLMGateway()


async def _generate_text(model: str, messages: list[dict]) -> str:
    accumulated = ""
    async for event in llm_gateway.stream_chat(model, messages, enable_tools=False):
        if isinstance(event, ContentEvent):
            accumulated += event.content
    return accumulated


def _parse_json_object(text: str) -> dict:
    candidate = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL)
    if fenced:
        candidate = fenced.group(1).strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        parsed = None
    else:
        if isinstance(parsed, dict):
            return parsed
        raise ValueError("The model did not return a valid JSON proposal object.")
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(candidate[start:end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    raise ValueError("The model did not return a valid JSON proposal object.")


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
    requested_address = request.api_address or saved["obsidian_api_address"]
    try:
        validated_address = _validate_test_address(requested_address)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not api_key:
        try:
            saved_address = _validate_test_address(saved["obsidian_api_address"])
        except ValueError:
            saved_address = None
        if validated_address != saved_address:
            raise HTTPException(
                status_code=400,
                detail="Enter the API key when testing a different Obsidian address.",
            )
    config = {
        "obsidian_api_address": validated_address,
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
    if "content" in proposal and not isinstance(proposal["content"], str):
        raise HTTPException(status_code=400, detail="The model returned invalid note content.")
    if "section" in proposal and not isinstance(proposal["section"], str):
        raise HTTPException(status_code=400, detail="The model returned an invalid section.")

    if action == "create":
        title_value = proposal.get("title") or "Untitled"
        if not isinstance(title_value, str):
            raise HTTPException(status_code=400, detail="The model returned an invalid note title.")
        title = title_value.strip()
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
    if action in {"create", "append", "edit", "replace"} and not proposal.get("content"):
        raise HTTPException(status_code=400, detail="The model did not generate note content.")
    if action == "edit" and not proposal.get("section"):
        raise HTTPException(status_code=400, detail="The model did not identify a section to edit.")

    proposal_id = _save_proposal(proposal)
    return {"proposal_id": proposal_id, "proposal": proposal}


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
    if action["action"] not in {"search", "open"}:
        raise HTTPException(
            status_code=400,
            detail="Vault writes must use a server-issued proposal and explicit confirmation.",
        )
    try:
        return await ObsidianService().execute(action)
    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/proposals/confirm")
async def confirm_proposal(request: ObsidianProposalConfirmation):
    proposal = _take_proposal(request.proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal was cancelled, expired, or already confirmed.")
    if request.content is not None:
        if proposal["action"] == "delete":
            raise HTTPException(status_code=400, detail="Delete proposals do not accept note content.")
        proposal["content"] = request.content
    try:
        return await ObsidianService().execute(proposal)
    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/proposals/cancel")
async def cancel_proposal(request: ObsidianProposalCancellation):
    return {"cancelled": _cancel_proposal(request.proposal_id)}
