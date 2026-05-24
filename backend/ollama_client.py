import httpx
import json
import os
import time
from typing import List, Dict, AsyncIterator

STREAM_BATCH_CHARS = int(os.getenv("STREAM_BATCH_CHARS", "40"))
STREAM_BATCH_SECONDS = float(os.getenv("STREAM_BATCH_SECONDS", "0.08"))


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = None):
        # Use environment variable if set (for Docker), otherwise default to localhost
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = httpx.Timeout(300.0, connect=5.0)
    
    async def get_models(self) -> List[Dict]:
        """Fetch all installed models from Ollama"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                
                models = []
                for model in data.get("models", []):
                    models.append({
                        "name": model["name"],
                        "size": model.get("size", 0),
                        "modified_at": model.get("modified_at", ""),
                        "digest": model.get("digest", "")
                    })
                
                return models
            except httpx.ConnectError:
                raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
            except Exception as e:
                raise Exception(f"Error fetching models: {str(e)}")
    
    async def chat_stream(self, model: str, messages: List[Dict]) -> AsyncIterator[str]:
        """
        Stream chat responses from Ollama
        
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
                "stream": True
            }
            
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    buffered_content = ""
                    last_flush = time.monotonic()

                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk = json.loads(line)
                                if "message" in chunk:
                                    content = chunk["message"].get("content", "")
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
                # Can't access .text on streaming responses without reading first
                error_msg = f"HTTP {e.response.status_code}"
                try:
                    error_detail = await e.response.aread()
                    error_msg += f" - {error_detail.decode('utf-8')}"
                except:
                    pass
                raise Exception(f"Ollama API error: {error_msg}")
            except httpx.ConnectError:
                raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
            except Exception as e:
                raise Exception(f"Error during chat: {str(e)}")
    
    async def chat(self, model: str, messages: List[Dict]) -> str:
        """
        Non-streaming chat (for testing or specific use cases)
        
        Args:
            model: Model name to use
            messages: List of message dicts with 'role' and 'content'
        
        Returns:
            Complete response text
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
            
            except httpx.HTTPStatusError as e:
                # For non-streaming responses, .text is accessible
                error_msg = f"HTTP {e.response.status_code}"
                try:
                    error_msg += f" - {e.response.text}"
                except:
                    pass
                raise Exception(f"Ollama API error: {error_msg}")
            except httpx.ConnectError:
                raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
            except Exception as e:
                raise Exception(f"Error during chat: {str(e)}")
    
    async def check_model_exists(self, model_name: str) -> bool:
        """Check if a specific model is installed"""
        models = await self.get_models()
        return any(m["name"] == model_name for m in models)
