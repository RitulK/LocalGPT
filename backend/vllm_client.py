import httpx
import json
import os
import time
from typing import List, Dict, AsyncIterator

STREAM_BATCH_CHARS = int(os.getenv("STREAM_BATCH_CHARS", "40"))
STREAM_BATCH_SECONDS = float(os.getenv("STREAM_BATCH_SECONDS", "0.08"))


class VLLMClient:
    """Client for interacting with vLLM OpenAI-compatible API"""
    
    def __init__(self, base_url: str = None):
        # Auto-detect if running in Docker and adjust URL accordingly
        is_docker = os.getenv("DOCKER_ENV") == "1" or os.path.exists("/.dockerenv")
        
        if base_url:
            self.base_url = base_url
        else:
            # Check for custom URL in environment
            custom_url = os.getenv("VLLM_BASE_URL")
            if custom_url:
                self.base_url = custom_url
            else:
                # Default: use host.docker.internal for Docker, localhost for local
                default_url = "http://host.docker.internal:5000/v1" if is_docker else "http://localhost:5000/v1"
                self.base_url = default_url
        
        self.timeout = httpx.Timeout(300.0, connect=5.0)
        self.api_key = os.getenv("VLLM_API_KEY", "dummy")  # vLLM doesn't require a real key by default
    
    async def get_models(self) -> List[Dict]:
        """Fetch available models from vLLM"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()
                
                models = []
                for model in data.get("data", []):
                    models.append({
                        "name": model["id"],
                        "size": 0,  # vLLM doesn't provide size info easily
                        "modified_at": "",
                        "digest": "",
                        "provider": "vllm"
                    })
                
                return models
            except httpx.ConnectError:
                raise Exception("Cannot connect to vLLM. Make sure vLLM server is running.")
            except Exception as e:
                raise Exception(f"Error fetching vLLM models: {str(e)}")
    
    async def chat_stream(self, model: str, messages: List[Dict]) -> AsyncIterator[str]:
        """
        Stream chat responses from vLLM (OpenAI-compatible API)
        
        Args:
            model: Model name to use
            messages: List of message dicts with 'role' and 'content'
        
        Yields:
            Chunks of text as they arrive
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 4096
            }
            
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    response.raise_for_status()
                    
                    buffered_content = ""
                    last_flush = time.monotonic()

                    async for line in response.aiter_lines():
                        if line.strip() and line.startswith("data:"):
                            try:
                                # Remove "data: " prefix
                                data = line[6:].strip()
                                if data == "[DONE]":
                                    break
                                
                                chunk = json.loads(data)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        buffered_content += content
                                        should_flush = (
                                            len(buffered_content) >= STREAM_BATCH_CHARS
                                            or time.monotonic() - last_flush >= STREAM_BATCH_SECONDS
                                        )
                                        if should_flush:
                                            yield buffered_content
                                            buffered_content = ""
                                            last_flush = time.monotonic()
                            except json.JSONDecodeError:
                                continue

                    if buffered_content:
                        yield buffered_content
            
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}"
                try:
                    error_detail = await e.response.aread()
                    error_msg += f" - {error_detail.decode('utf-8')}"
                except:
                    pass
                raise Exception(error_msg)
            except Exception as e:
                raise Exception(f"vLLM streaming error: {str(e)}")
