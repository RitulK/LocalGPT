import json
import re
import httpx
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI

from app.domain.models import ContentEvent, ReasoningEvent, ToolCallEvent
from app.core.config import settings
from app.infrastructure.llm.tools import TINYFISH_TOOLS


def parse_model_spec(model_spec: str) -> Tuple[str, str, Optional[str]]:
    if not model_spec:
        return "ollama", "", None
    host = model_spec.rsplit("@", 1)[1] if "@" in model_spec else None
    model_part = model_spec.rsplit("@", 1)[0] if "@" in model_spec else model_spec
    known = {"ollama", "openai", "vllm", "nvidia"}
    if ":" in model_part and model_part.split(":", 1)[0].lower() in known:
        prefix, rest = model_part.split(":", 1)
        return prefix.lower(), rest, host
    return "ollama", model_part, host


class LLMGateway:
    """Unified Gateway for LLM providers using provider:model@host convention."""

    def __init__(self, ollama_url: Optional[str] = None, vllm_url: Optional[str] = None, nvidia_url: Optional[str] = None, nvidia_api_key: Optional[str] = None):
        self.ollama_url = ollama_url or settings.OLLAMA_BASE_URL
        self.vllm_url = vllm_url or settings.VLLM_BASE_URL
        self.nvidia_url = nvidia_url or settings.NVIDIA_BASE_URL
        self.nvidia_api_key = nvidia_api_key or settings.NVIDIA_API_KEY

    def _get_client(self, model_spec: str, provider: Optional[str] = None, enable_tools: bool = True):
        parsed_provider, model_name, custom_host = parse_model_spec(model_spec)
        prov = (provider or parsed_provider).lower()
        if prov in ("vllm", "openai"):
            client = ChatOpenAI(model=model_name, base_url=custom_host or self.vllm_url, api_key="EMPTY")
        elif prov == "nvidia":
            client = ChatOpenAI(model=model_name, base_url=custom_host or self.nvidia_url, api_key=self.nvidia_api_key or "EMPTY")
        else:
            client = ChatOllama(model=model_name, base_url=custom_host or self.ollama_url)
        supports_tools = prov != "ollama" or ":cloud" in model_name
        return (
            client.bind_tools(TINYFISH_TOOLS)
            if settings.TINYFISH_API_KEY and enable_tools and supports_tools
            else client
        )

    def _convert_messages(self, messages: List[Dict[str, Any]]):
        converted = []
        for message in messages:
            role = message.get("role")
            if role == "system":
                converted.append(SystemMessage(content=message.get("content", "")))
            elif role == "assistant":
                converted.append(AIMessage(
                    content=message.get("content", ""),
                    tool_calls=message.get("tool_calls", []),
                ))
            elif role == "tool":
                from langchain_core.messages import ToolMessage
                converted.append(ToolMessage(
                    content=message.get("content", ""),
                    tool_call_id=message["tool_call_id"],
                ))
            else:
                converted.append(HumanMessage(content=message.get("content", "")))
        return converted

    @staticmethod
    def _parse_text_tool_call(text: str) -> Optional[Dict[str, Any]]:
        candidate = text.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL)
        if fenced:
            candidate = fenced.group(1).strip()
        candidates = [candidate]
        match = re.search(r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:', candidate)
        if match:
            candidates.append(candidate[match.start():])
        for item in candidates:
            try:
                payload, _ = json.JSONDecoder().raw_decode(item)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            name = payload.get("name")
            arguments = payload.get("arguments")
            if (
                isinstance(name, str)
                and isinstance(arguments, dict)
                and name in {"search", "fetch_content", "run_web_automation"}
            ):
                return {"name": name, "arguments": arguments}
        return None

    async def stream_chat(self, model_or_provider: str, messages_or_model: Any, messages: Optional[List[Dict[str, Any]]] = None, enable_tools: bool = True) -> AsyncIterator[Union[ContentEvent, ReasoningEvent, ToolCallEvent]]:
        provider, model_spec, msg_list = (model_or_provider, messages_or_model, messages) if messages is not None else (None, model_or_provider, messages_or_model)
        client = self._get_client(model_spec, provider=provider, enable_tools=enable_tools)
        parsed_provider, parsed_model, _ = parse_model_spec(model_spec)
        native_tools_enabled = bool(
            settings.TINYFISH_API_KEY
            and enable_tools
            and (
                (provider or parsed_provider) != "ollama"
                or (
                    (provider or parsed_provider) == "ollama"
                    and ":cloud" in parsed_model
                )
            )
        )
        tool_calls: Dict[str, Dict[str, Any]] = {}
        tool_indexes: Dict[int, str] = {}
        text_content = ""
        async for chunk in client.astream(self._convert_messages(msg_list)):
            reasoning = chunk.additional_kwargs.get("reasoning_content") or getattr(chunk, "reasoning_content", None)
            if reasoning:
                yield ReasoningEvent(content=str(reasoning))
            if chunk.content:
                text = chunk.content if isinstance(chunk.content, str) else "".join(p if isinstance(p, str) else p.get("text", "") for p in chunk.content if isinstance(p, (str, dict)))
                if text:
                    text_content += text
                    if not native_tools_enabled:
                        yield ContentEvent(content=text)
            for call in getattr(chunk, "tool_calls", []) or getattr(chunk, "tool_call_chunks", []):
                index = call.get("index", 0)
                call_id = call.get("id") or tool_indexes.get(index) or f"tool_{index}"
                tool_indexes[index] = call_id
                current = tool_calls.setdefault(call_id, {"id": call_id, "name": "", "arguments": ""})
                current["name"] = current["name"] or call.get("name", "")
                args = call.get("args", "")
                if isinstance(args, str):
                    current["arguments"] += args
                elif isinstance(args, dict):
                    current["arguments"] = json.dumps(args)

        if not tool_calls and native_tools_enabled:
            parsed_text_call = self._parse_text_tool_call(text_content)
            if parsed_text_call:
                yield ToolCallEvent(
                    tool_call_id="text_tool_call_0",
                    name=parsed_text_call["name"],
                    arguments=parsed_text_call["arguments"],
                )
                return
        if not tool_calls and native_tools_enabled and text_content:
            yield ContentEvent(content=text_content)

        for call in tool_calls.values():
            try:
                arguments = json.loads(call["arguments"] or "{}")
            except json.JSONDecodeError:
                arguments = {}
            yield ToolCallEvent(
                tool_call_id=call["id"],
                name=call["name"],
                arguments=arguments,
            )

    async def get_models(self, provider: str = "ollama") -> List[Dict[str, Any]]:
        if provider.lower() != "ollama":
            # Cloud providers typically don't have a simple "tags" API like Ollama
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_url}/api/tags")
                response.raise_for_status()
                data = response.json()

                models = []
                for m in data.get("models", []):
                    models.append({
                        "name": f"ollama:{m['name']}",
                        "size": m.get("size", 0),
                        "details": m.get("details", {}),
                        "modified_at": m.get("modified_at")
                    })
                return models
        except Exception:
            return []

    async def pull_model(self, model_id: str) -> Dict[str, Any]:
        """Triggers an Ollama model pull. returns the final status."""
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                # Ollama /api/pull returns a stream of status updates
                # We can either stream it back to the user or just wait for completion
                response = await client.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": model_id, "stream": False}
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    async def pull_model_stream(self, model_id: str):
        """Yield Ollama pull progress without buffering the download."""
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_url}/api/pull",
                    json={"name": model_id, "stream": True},
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            yield {"status": "error", "error": "Invalid Ollama progress response"}
                            return
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            yield {
                "status": "error",
                "error": f"Ollama rejected the model download ({exc.response.status_code}): {detail}",
            }
        except httpx.HTTPError as exc:
            yield {"status": "error", "error": f"Could not connect to Ollama: {exc}"}

    async def embed(self, model: str, texts: List[str]) -> List[List[float]]:
        _, real_model, _ = parse_model_spec(model)
        return await OllamaEmbeddings(model=real_model or model, base_url=self.ollama_url).aembed_documents(texts)
