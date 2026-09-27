import os
from typing import AsyncIterator, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI


class LLMGateway:
    """Unified Gateway for Ollama, vLLM, and Nvidia LLM providers via LangChain."""

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

    def _get_client(self, provider: str, model: str):
        prov = (provider or "ollama").lower()
        if prov == "ollama":
            return ChatOllama(model=model, base_url=self.ollama_url)
        elif prov == "vllm":
            return ChatOpenAI(model=model, base_url=self.vllm_url, api_key="EMPTY")
        elif prov == "nvidia":
            return ChatOpenAI(model=model, base_url=self.nvidia_url, api_key=self.nvidia_api_key or "EMPTY")
        return ChatOllama(model=model, base_url=self.ollama_url)

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
        self, provider: str, model: str, messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        client = self._get_client(provider, model)
        langchain_messages = self._convert_messages(messages)
        async for chunk in client.astream(langchain_messages):
            if chunk.content:
                if isinstance(chunk.content, str):
                    yield chunk.content
                elif isinstance(chunk.content, list):
                    for part in chunk.content:
                        if isinstance(part, str):
                            yield part
                        elif isinstance(part, dict) and "text" in part:
                            yield part["text"]

    async def embed(self, model: str, texts: List[str]) -> List[List[float]]:
        embeddings = OllamaEmbeddings(model=model, base_url=self.ollama_url)
        return await embeddings.aembed_documents(texts)
