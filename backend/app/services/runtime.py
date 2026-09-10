import database
from ollama_client import OllamaClient
from rag_service import RAGService
from router import ModelRouter
from vllm_client import VLLMClient

try:
    from nvidia_client import NvidiaClient
except ModuleNotFoundError as exc:
    NvidiaClient = None
    print(f"Warning: Nvidia client dependencies unavailable - {exc}")


ollama_client = OllamaClient()
vllm_client = VLLMClient()
try:
    nvidia_client = NvidiaClient() if NvidiaClient else None
except ValueError as exc:
    nvidia_client = None
    print(f"Warning: Nvidia client not available - {exc}")

model_router = ModelRouter()
rag_service = RAGService()
MAX_CONTEXT_MESSAGES = 6
FORMAT_SYSTEM_PROMPT = (
    "Format answers in clean Markdown. When the user asks for a table, output a "
    "valid GitHub-Flavored Markdown table with each row on its own line, a header "
    "separator row, and no table inside a code block."
)
RAG_SYSTEM_PROMPT = (
    "You are answering with a user-selected local knowledge base. Use the retrieved "
    "sources below as the primary ground truth. Cite relevant sources with bracketed "
    "numbers like [1]. If the sources do not contain enough information, say that "
    "the uploaded documents do not provide enough detail and then clearly separate "
    "any general knowledge."
)


def default_settings() -> dict:
    from app.domain.schemas import Settings

    return Settings().dict()
