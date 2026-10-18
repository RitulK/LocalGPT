from typing import Any, Dict, Optional
from urllib.parse import quote_plus

import httpx

from app.core.config import settings


class TinyFishService:
    """Small HTTP client for TinyFish browser automation runs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.TINYFISH_API_KEY
        self.base_url = (base_url or settings.TINYFISH_BASE_URL).rstrip("/")

    async def run(self, url: str, goal: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "error", "error": "TinyFish is not configured"}

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.base_url}/run",
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={"url": url, "goal": goal},
                )
                response.raise_for_status()
                payload = response.json()
                status = str(payload.get("status", "")).upper()
                if status in {"FAILED", "ERROR", "CANCELLED", "TIMED_OUT"}:
                    error = payload.get("error") or f"TinyFish run {status.lower()}"
                    return {
                        "status": "error",
                        "error": error,
                        "run_status": status,
                    }
                return payload
        except (httpx.HTTPError, ValueError) as exc:
            return {"status": "error", "error": str(exc)}

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "search":
            query = str(arguments.get("query", "")).strip()
            if not query:
                return {"status": "error", "error": "Search query is required"}
            return await self.run(
                f"https://www.google.com/search?q={quote_plus(query)}",
                f"Search the page for: {query}. Return the most relevant results with titles, URLs, and useful snippets.",
            )

        if tool_name == "fetch_content":
            url = str(arguments.get("url", "")).strip()
            if not url:
                return {"status": "error", "error": "URL is required"}
            return await self.run(
                url,
                "Read the page and return its main text content, preserving important facts, dates, links, and headings.",
            )

        if tool_name == "run_web_automation":
            url = str(arguments.get("url", "")).strip()
            goal = str(arguments.get("goal", "")).strip()
            if not url or not goal:
                return {"status": "error", "error": "Both url and goal are required"}
            return await self.run(url, goal)

        return {"status": "error", "error": f"Unknown TinyFish tool: {tool_name}"}
