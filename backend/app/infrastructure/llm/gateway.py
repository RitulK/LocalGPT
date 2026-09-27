import os
from typing import AsyncIterator, Dict, List, Optional, Tuple, Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI


def parse_model_spec(model_spec: str) -> Tuple[str, str, Optional[str]]:
    """Parses model specification in 'provider:model@host' format."""
    if not model_spec:
        return "ollama", "", None
    host = None
    if "@" in model_spec:
        model_part, host = model_spec.rsplit("@", 1)
    else:
        model_part = model_spec
    known = {"ollama", "openai", "vllm", "nvidia"}
    if ":" in model_part:
        prefix, rest = model_part.split(":", 1)
        if prefix.lower() in known:
            return prefix.lower(), rest, host
    return "ollama", model_part, host


class LLMGateway:
    """Unified Gateway for LLM providers using provider:model@host convention."""

    def __init__(
        self,
        ollama_url: Optional[str] = None,
        vllm_url: Optional[str] = None,
        nvidia_url: Optional[str] = None,
        nvidia_api_key: Optional[str] = None,
    ):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.vllm_url = vllm_url or os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        self.nvidia_url = nvidia_url or os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.nvidia_api_key = nvidia_api_key or os.getenv("NVIDIA_API_KEY", "")

    def _get_client(self, model_spec: str, provider: Optional[str] = None):
        parsed_provider, model_name, custom_host = parse_model_spec(model_spec)
        prov = (provider or parsed_provider).lower()
        if prov in ("vllm", "openai"):
            return ChatOpenAI(model=model_name, base_url=custom_host or self.vllm_url, api_key="EMPTY")
        elif prov == "nvidia":
            return ChatOpenAI(model=model_name, base_url=custom_host or self.nvidia_url, api_key=self.nvidia_api_key or "EMPTY")
        return ChatOllama(model=model_name, base_url=custom_host or self.ollama_url)

    def _convert_messages(self, messages: List[Dict[str, str]]):
        converted = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            else:
                converted.append(HumanMessage(content=content))
        return converted

    async def stream_chat(
        self, model_or_provider: str, messages_or_model: Any, messages: Optional[List[Dict[str, str]]] = None
    ) -> AsyncIterator[str]:
        if messages is not None:
            provider, model_spec, msg_list = model_or_provider, messages_or_model, messages
        else:
            provider, model_spec, msg_list = None, model_or_provider, messages_or_model
        client = self._get_client(model_spec, provider=provider)
        async for chunk in client.astream(self._convert_messages(msg_list)):
            if chunk.content:
                if isinstance(chunk.content, str):
                    yield chunk.content
                elif isinstance(chunk.content, list):
                    for part in chunk.content:
                        if isinstance(part, str):
                            yield part
                        elif isinstance(part, dict) and "text" in part:
                            yield part["text"]

    async def get_models(self, provider: str = "ollama") -> List[Dict[str, Any]]:
        prefix = "openai:" if provider.lower() in ("vllm", "nvidia", "openai") else "ollama:"
        return [{"name": f"{prefix}default-model"}]

    async def embed(self, model: str, texts: List[str]) -> List[List[float]]:
        _, real_model, _ = parse_model_spec(model)
        embeddings = OllamaEmbeddings(model=real_model or model, base_url=self.ollama_url)
        return await embeddings.aembed_documents(texts)
