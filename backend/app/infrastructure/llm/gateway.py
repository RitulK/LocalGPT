import os
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI

from app.domain.models import ContentEvent, ReasoningEvent
from app.core.config import settings


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

    def _get_client(self, model_spec: str, provider: Optional[str] = None):
        parsed_provider, model_name, custom_host = parse_model_spec(model_spec)
        prov = (provider or parsed_provider).lower()
        if prov in ("vllm", "openai"):
            return ChatOpenAI(model=model_name, base_url=custom_host or self.vllm_url, api_key="EMPTY")
        elif prov == "nvidia":
            return ChatOpenAI(model=model_name, base_url=custom_host or self.nvidia_url, api_key=self.nvidia_api_key or "EMPTY")
        return ChatOllama(model=model_name, base_url=custom_host or self.ollama_url)

    def _convert_messages(self, messages: List[Dict[str, str]]):
        role_map = {"system": SystemMessage, "assistant": AIMessage}
        return [role_map.get(m.get("role"), HumanMessage)(content=m.get("content", "")) for m in messages]

    async def stream_chat(self, model_or_provider: str, messages_or_model: Any, messages: Optional[List[Dict[str, str]]] = None) -> AsyncIterator[Union[ContentEvent, ReasoningEvent]]:
        provider, model_spec, msg_list = (model_or_provider, messages_or_model, messages) if messages is not None else (None, model_or_provider, messages_or_model)
        client = self._get_client(model_spec, provider=provider)
        async for chunk in client.astream(self._convert_messages(msg_list)):
            reasoning = chunk.additional_kwargs.get("reasoning_content") or getattr(chunk, "reasoning_content", None)
            if reasoning:
                yield ReasoningEvent(content=str(reasoning))
            if chunk.content:
                text = chunk.content if isinstance(chunk.content, str) else "".join(p if isinstance(p, str) else p.get("text", "") for p in chunk.content if isinstance(p, (str, dict)))
                if text:
                    yield ContentEvent(content=text)

    async def get_models(self, provider: str = "ollama") -> List[Dict[str, Any]]:
        prefix = "openai:" if provider.lower() in ("vllm", "nvidia", "openai") else "ollama:"
        return [{"name": f"{prefix}default-model"}]

    async def embed(self, model: str, texts: List[str]) -> List[List[float]]:
        _, real_model, _ = parse_model_spec(model)
        return await OllamaEmbeddings(model=real_model or model, base_url=self.ollama_url).aembed_documents(texts)
