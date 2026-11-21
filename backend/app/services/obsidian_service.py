from pathlib import PurePosixPath
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from app.infrastructure.db.connection import get_connection
from app.infrastructure.db.repositories import SettingsRepository
from app.domain.schemas import Settings


settings_repo = SettingsRepository()
MASKED_KEY = "********"


def get_saved_settings() -> Dict[str, Any]:
    with get_connection() as conn:
        return settings_repo.get(conn, Settings().model_dump())


def public_settings() -> Dict[str, Any]:
    saved = get_saved_settings()
    if saved.get("obsidian_api_key"):
        saved["obsidian_api_key"] = MASKED_KEY
    return saved


def update_saved_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    if settings.get("obsidian_api_key") == MASKED_KEY:
        settings["obsidian_api_key"] = get_saved_settings().get("obsidian_api_key", "")
    with get_connection() as conn:
        saved = settings_repo.save(conn, settings)
    return public_settings() if "obsidian_api_key" in saved else saved


def normalize_vault_path(path: str) -> str:
    if not path or "\x00" in path:
        raise ValueError("A vault path is required.")
    path = path.replace("\\", "/").strip()
    if path.startswith("/") or ":" in path:
        raise ValueError("Vault paths must be relative to the vault.")
    normalized = PurePosixPath(path)
    if ".." in normalized.parts:
        raise ValueError("Vault paths cannot contain '..'.")
    parts = [part for part in normalized.parts if part != ""]
    if not parts:
        raise ValueError("A vault path is required.")
    if parts[0].lower() == ".obsidian" or ".obsidian" in (part.lower() for part in parts):
        raise ValueError("The Obsidian configuration folder is not accessible.")
    return "/".join(parts)


def validate_write_path(path: str, allowed_folder: str) -> str:
    normalized = normalize_vault_path(path)
    allowed = allowed_folder.replace("\\", "/").strip("/")
    if allowed and not (normalized == allowed or normalized.startswith(f"{allowed}/")):
        raise ValueError(f"Writes are restricted to the '{allowed}/' folder.")
    return normalized


class ObsidianService:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_saved_settings()

    def _verify_tls(self) -> Any:
        if not self.config.get("obsidian_verify_tls", True):
            return False
        ca_path = str(self.config.get("obsidian_ca_path", "")).strip()
        return ca_path or True

    def _headers(self) -> Dict[str, str]:
        key = str(self.config.get("obsidian_api_key", "")).strip()
        return {"Authorization": f"Bearer {key}"} if key else {}

    async def test_connection(self) -> Dict[str, Any]:
        address = str(self.config.get("obsidian_api_address", "")).strip().rstrip("/")
        if not address:
            raise ValueError("Obsidian API address is required.")
        if not address.startswith(("https://", "http://")):
            raise ValueError("Obsidian API address must use http:// or https://.")
        async with httpx.AsyncClient(
            timeout=8,
            verify=self._verify_tls(),
        ) as client:
            response = await client.get(f"{address}/", headers=self._headers())
        if response.status_code >= 400:
            raise ValueError(f"Obsidian connection failed ({response.status_code}).")
        try:
            data = response.json()
        except ValueError:
            data = {}
        return {
            "connected": bool(data.get("authenticated", True)),
            "status": data.get("status"),
            "display_name": self.config.get("obsidian_display_name", ""),
            "state": data.get("state", {}),
        }

    async def search(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        if not self.config.get("obsidian_allow_read", True):
            raise ValueError("Obsidian search and read permission is disabled.")
        address = str(self.config["obsidian_api_address"]).rstrip("/")
        headers = self._headers()
        async with httpx.AsyncClient(timeout=15, verify=self._verify_tls()) as client:
            response = await client.post(
                f"{address}/search/simple/",
                headers=headers,
                params={"query": query, "maxResults": max(1, min(max_results, 100))},
            )
        if response.status_code >= 400:
            raise ValueError(self._api_error(response))
        try:
            results = response.json()
        except ValueError:
            results = []
        return {"query": query, "results": results}

    async def read(self, path: str) -> Dict[str, Any]:
        if not self.config.get("obsidian_allow_read", True):
            raise ValueError("Obsidian search and read permission is disabled.")
        normalized = normalize_vault_path(path)
        address = str(self.config["obsidian_api_address"]).rstrip("/")
        async with httpx.AsyncClient(timeout=15, verify=self._verify_tls()) as client:
            response = await client.get(
                f"{address}/vault/{quote(normalized, safe='/')}",
                headers={**self._headers(), "Accept": "text/markdown"},
            )
        if response.status_code >= 400:
            raise ValueError(self._api_error(response))
        return {
            "path": normalized,
            "content": response.text,
            "if_match": response.headers.get("etag") or response.headers.get("ETag"),
        }

    async def open(self, path: str) -> Dict[str, Any]:
        if not self.config.get("obsidian_allow_read", True):
            raise ValueError("Obsidian search and read permission is disabled.")
        normalized = normalize_vault_path(path)
        address = str(self.config["obsidian_api_address"]).rstrip("/")
        async with httpx.AsyncClient(timeout=15, verify=self._verify_tls()) as client:
            response = await client.post(
                f"{address}/open/{quote(normalized, safe='/')}",
                headers=self._headers(),
            )
        if response.status_code >= 400:
            raise ValueError(self._api_error(response))
        return {"path": normalized, "opened": True}

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        kind = action["action"]
        if kind == "search":
            return await self.search(str(action.get("query", "")), 20)
        if kind == "open":
            return await self.open(str(action["path"]))

        allowed = str(self.config.get("obsidian_allowed_folder", "")).strip()
        if kind in {"create", "append", "edit", "replace", "delete"}:
            if not self.config.get("obsidian_allow_write", True) and kind != "delete":
                raise ValueError("Obsidian write permission is disabled.")
            if kind == "delete" and not self.config.get("obsidian_allow_delete", False):
                raise ValueError("Obsidian delete permission is disabled.")
        if kind == "create":
            path = validate_write_path(str(action["path"]), allowed)
            content = str(action.get("content", ""))
            response = await self._write_request(
                "PUT",
                path,
                content,
                if_none_match="*",
            )
            return {"action": kind, "path": path, "created": True, "response": response}
        if kind in {"append", "replace", "edit", "delete"}:
            path = validate_write_path(str(action["path"]), allowed)
            if_match = action.get("if_match")
            if not if_match:
                raise ValueError("The note version changed or is missing. Review the action again.")
            if kind == "append":
                content = str(action.get("content", ""))
                section = str(action.get("section", "")).strip()
                if section:
                    response = await self._write_request(
                        "POST",
                        path,
                        content,
                        section=section,
                        if_match=if_match,
                    )
                else:
                    response = await self._write_request(
                        "POST",
                        path,
                        content,
                        if_match=if_match,
                    )
                return {"action": kind, "path": path, "section": section or None, "updated": True, "response": response}
            if kind == "edit":
                section = str(action.get("section", "")).strip()
                if not section:
                    raise ValueError("A heading section is required for an edit.")
                instruction = {
                    "targetType": "heading",
                    "target": [section],
                    "operation": "replace",
                    "scope": "content",
                    "content": str(action.get("content", "")),
                    "ifMatch": if_match,
                }
                response = await self._patch_request(path, instruction, if_match)
                return {"action": kind, "path": path, "section": section, "updated": True, "response": response}
            if kind == "replace":
                response = await self._write_request(
                    "PUT",
                    path,
                    str(action.get("content", "")),
                    if_match=if_match,
                )
                return {"action": kind, "path": path, "replaced": True, "response": response}
            response = await self._delete_request(path, if_match)
            return {"action": kind, "path": path, "deleted": True, "response": response}
        raise ValueError(f"Unsupported Obsidian action: {kind}")

    async def _write_request(
        self,
        method: str,
        path: str,
        content: str,
        section: Optional[str] = None,
        if_match: Optional[str] = None,
        if_none_match: Optional[str] = None,
    ) -> Dict[str, Any]:
        address = str(self.config["obsidian_api_address"]).rstrip("/")
        url = f"{address}/vault/{quote(path, safe='/')}"
        if section:
            url += f"/heading/{quote(section, safe='')}"
        headers = {**self._headers(), "Content-Type": "text/markdown"}
        if if_match:
            headers["If-Match"] = if_match
        if if_none_match:
            headers["If-None-Match"] = if_none_match
        async with httpx.AsyncClient(timeout=15, verify=self._verify_tls()) as client:
            response = await client.request(method, url, headers=headers, content=content)
        if response.status_code >= 400:
            raise ValueError(self._api_error(response))
        return {
            "status": response.status_code,
            "if_match": response.headers.get("etag") or response.headers.get("ETag"),
        }

    async def _patch_request(
        self,
        path: str,
        instruction: Dict[str, Any],
        if_match: Optional[str],
    ) -> Dict[str, Any]:
        address = str(self.config["obsidian_api_address"]).rstrip("/")
        headers = {**self._headers(), "Content-Type": "application/json"}
        if if_match:
            headers["If-Match"] = if_match
        async with httpx.AsyncClient(timeout=15, verify=self._verify_tls()) as client:
            response = await client.patch(
                f"{address}/vault/{quote(path, safe='/')}",
                headers=headers,
                json=instruction,
            )
        if response.status_code >= 400:
            raise ValueError(self._api_error(response))
        return {
            "status": response.status_code,
            "if_match": response.headers.get("etag") or response.headers.get("ETag"),
        }

    async def _delete_request(self, path: str, if_match: Optional[str]) -> Dict[str, Any]:
        address = str(self.config["obsidian_api_address"]).rstrip("/")
        headers = dict(self._headers())
        if if_match:
            headers["If-Match"] = if_match
        async with httpx.AsyncClient(timeout=15, verify=self._verify_tls()) as client:
            response = await client.delete(
                f"{address}/vault/{quote(path, safe='/')}",
                headers=headers,
            )
        if response.status_code >= 400:
            raise ValueError(self._api_error(response))
        return {"status": response.status_code}

    @staticmethod
    def _api_error(response: httpx.Response) -> str:
        try:
            data = response.json()
            message = data.get("message") if isinstance(data, dict) else None
            if message:
                return f"{message} ({response.status_code})"
        except ValueError:
            pass
        return f"Obsidian API request failed ({response.status_code})."
