from app.infrastructure.llm.gateway import LLMGateway
from rag_service import RAGService
from app.core.config import settings

llm_gateway = LLMGateway()
rag_service = RAGService()
MAX_CONTEXT_MESSAGES = 6
FORMAT_SYSTEM_PROMPT = (
    "Format answers in clean Markdown. When the user asks for a table, output a "
    "valid GitHub-Flavored Markdown table with each row on its own line, a header "
    "separator row, and no table inside a code block."
)
WEB_TOOLS_SYSTEM_PROMPT = (
    "You have access to live web tools through TinyFish. You MUST use the search "
    "tool before answering questions about today's date, current time, current "
    "events, recent news, prices, availability, or any other information that "
    "could have changed. Do not claim that you lack real-time access when a web "
    "tool is available. After receiving tool results, answer using those results "
    "and clearly mention any uncertainty."
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

    return Settings().model_dump()
