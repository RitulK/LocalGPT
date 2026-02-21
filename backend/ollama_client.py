import httpx
import json
from typing import List, Dict, AsyncIterator


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
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
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk = json.loads(line)
                                if "message" in chunk:
                                    content = chunk["message"].get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
            
            except httpx.HTTPStatusError as e:
                raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
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
                raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            except httpx.ConnectError:
                raise Exception("Cannot connect to Ollama. Make sure Ollama is running.")
            except Exception as e:
                raise Exception(f"Error during chat: {str(e)}")
    
    async def check_model_exists(self, model_name: str) -> bool:
        """Check if a specific model is installed"""
        models = await self.get_models()
        return any(m["name"] == model_name for m in models)
