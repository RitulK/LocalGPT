# Changelog

All notable repository changes are recorded here, newest first.

## 2026-09-27

### P2-S1 LLMGateway build & provider client consolidation

- Added `langchain-core`, `langchain-ollama`, and `langchain-openai` to `requirements.txt`.
- Created unified `LLMGateway` in `backend/app/infrastructure/llm/gateway.py` (66 LOC, 0 `httpx` imports).
- Deleted `ollama_client.py`, `vllm_client.py`, and `nvidia_client.py` (~600 LOC net deletion).
- Updated `ChatService`, `document_service`, `model_service`, and `health.py` to route LLM operations through `LLMGateway`.
- Created `test_llm_gateway.py` unit test suite and verified all 21 tests pass cleanly.

### P1-S3 SQL Repository extraction

- Extracted repository classes (`ConversationRepository`, `MessageRepository`, `DocumentRepository`, `MemoryRepository`, `SettingsRepository`) in `backend/app/infrastructure/db/repositories.py`.
- Updated all service modules under `backend/app/services/` to call repositories directly instead of `database.*`.
- Converted `backend/database.py` to a thin re-export wrapper using the repositories.
- Created `backend/test_repositories.py` with full unit test coverage.
- Verified `grep -r "import database" app/services/` returns no matches and all pytest tests pass.

### P1-S2 ChatService extraction

- Extracted chat streaming, routing, RAG retrieval, and message persistence into `ChatService` in `backend/app/services/chat_service.py`.
- Removed all `fastapi` dependencies from `ChatService`.
- Simplified route handler in `backend/app/api/chat.py` to delegate streaming to `ChatService`.
- Added unit test suite in `backend/test_chat_service.py`.
- All tests passed (`backend/.venv/bin/python -m pytest -q`).

## 2026-09-11

### P1-S1 backend layering

- Added the layered `backend/app/` package and API routers.
- Reduced `backend/main.py` to application construction and router wiring.
- Added service and domain modules for the extracted route behavior.
- Added structural tests for the application factory and router layout.
- Installed pytest in `backend/.venv`.
- Fixed router score aggregation and converted the router smoke script into
  pytest-discoverable unit tests.
- Full test command: `backend/.venv/bin/python -m pytest -q`.
