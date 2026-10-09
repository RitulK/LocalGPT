from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./localgpt.db"

    # LLM Gateways
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    VLLM_BASE_URL: str = "http://localhost:8000/v1"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_API_KEY: str = ""

    # RAG Settings
    RAG_EMBEDDING_MODEL: str = "nomic-embed-text"
    RAG_CHUNK_WORDS: int = 800
    RAG_CHUNK_OVERLAP_WORDS: int = 120
    RAG_RETRIEVAL_LIMIT: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
