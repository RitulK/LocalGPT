import os
from typing import List, Dict, AsyncIterator, Optional
import json
import time
from openai import AsyncOpenAI, APIConnectionError, AuthenticationError

STREAM_BATCH_CHARS = int(os.getenv("STREAM_BATCH_CHARS", "40"))
STREAM_BATCH_SECONDS = float(os.getenv("STREAM_BATCH_SECONDS", "0.08"))


class NvidiaClient:
    """Client for interacting with Nvidia's cloud API (OpenAI-compatible)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY environment variable not set. "
                "Get your API key from https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b"
            )
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        self.model = "nvidia/nemotron-3-ultra-550b-a55b"
    
    async def get_models(self) -> List[Dict]:
        """Return available Nvidia models"""
        return [
            {
                "name": self.model,
                "size": 550e9,  # 550B parameters
                "modified_at": "",
                "digest": "",
                "provider": "nvidia"
            }
        ]
    
    async def chat_stream(
        self, 
        model: str, 
        messages: List[Dict],
        enable_thinking: bool = False,
        reasoning_budget: int = 8192
    ) -> AsyncIterator[str]:
        """
        Stream chat responses from Nvidia API with optional reasoning support
        
        Args:
            model: Model name (typically "nvidia/nemotron-3-ultra-550b-a55b")
            messages: List of message dicts with 'role' and 'content'
            enable_thinking: Whether to enable extended thinking/reasoning
            reasoning_budget: Max tokens for thinking (default 8192)
        
        Yields:
            Chunks of text as they arrive (includes reasoning content if enabled)
        """
        try:
            # Build extra_body for reasoning support
            extra_body = {}
            if enable_thinking:
                extra_body = {
                    "chat_template_kwargs": {
                        "enable_thinking": True
                    },
                    "reasoning_budget": reasoning_budget
                }
            
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                top_p=0.95,
                max_tokens=8192,
                stream=True,
                extra_body=extra_body if extra_body else None
            )
            
            buffered_content = ""
            last_flush = time.monotonic()
            
            async for chunk in stream:
                if not chunk.choices:
                    continue
                
                choice = chunk.choices[0]
                delta = choice.delta
                
                # Handle reasoning content (thinking)
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    # Yield reasoning with special marker for frontend
                    data = {
                        "type": "reasoning",
                        "content": reasoning
                    }
                    yield f"[REASONING]{json.dumps(data)}[/REASONING]"
                
                # Handle regular content
                if delta.content is not None:
                    content = delta.content
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
            
            # Flush remaining content
            if buffered_content:
                yield buffered_content
        
        except AuthenticationError:
            raise Exception(
                "Nvidia API authentication failed. "
                "Check your NVIDIA_API_KEY environment variable. "
                "Get a free API key from https://build.nvidia.com"
            )
        except APIConnectionError:
            raise Exception(
                "Failed to connect to Nvidia API. "
                "Make sure you have internet connectivity and API key is valid."
            )
        except Exception as e:
            raise Exception(f"Nvidia API error: {str(e)}")
