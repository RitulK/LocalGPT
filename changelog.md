# Changelog

All notable repository changes are recorded here, newest first.

## 2026-10-02

### P3-S2 LangChain Retriever integration in RAGService

- Refactored `RAGService.retrieve` to use `chroma_store.as_retriever(document_ids, k).ainvoke(prompt)` (8 LOC).
- Removed manual `self.get_collection().query(...)` code completely (`rg "self.get_collection\(\).query" app/` returns 0 hits).
- Updated `public_sources` and `format_rag_context` in `app/domain/rag.py` to seamlessly handle LangChain `Document` objects.
- Updated `test_rag_service.py` unit tests and verified all 26 tests pass cleanly.

### P3-S1 ChromaStore wrapper & retriever extraction

- Added `langchain-chroma` to `requirements.txt`.
- Created `ChromaStore` in `backend/app/infrastructure/vector/chroma_store.py` (57 LOC) exposing `as_retriever(document_ids, k)`.
- Updated `RAGService` to delegate persistent Chroma collection operations to `ChromaStore`.
- Created `test_chroma_store.py` unit test suite.
- All 25 pytest unit tests pass cleanly.

## 2026-09-27

### P2-S3 Typed SSE events (discriminated union)

- Created `app/domain/models.py` with `StreamEvent` discriminated union models (`MetadataEvent`, `ContentEvent`, `ReasoningEvent`, `DoneEvent`, `ErrorEvent`).
- Updated `LLMGateway.stream_chat` to yield typed events (`ContentEvent`, `ReasoningEvent`) and extract `reasoning_content` delta attributes.
- Refactored `ChatService.stream_chat` to emit serialized JSON events using `model_dump_json()`.
- Verified `rg "\[REASONING\]" app/` and `rg "\[/REASONING\]" app/` both return 0 hits.
- All 22 pytest unit tests pass cleanly.

### P2-S2 Provider-name convention & registry

- Implemented `provider:model@host` parsing logic (`parse_model_spec`) in `LLMGateway`.
- Removed all hardcoded string-sniffing for `"nemotron"` and `"nvidia/"` across `backend/app/`.
- Updated `ChatService` and `LLMGateway` to resolve adapters dynamically via model name prefixes (`ollama:`, `openai:`, `nvidia:`).
- Added `test_parse_model_spec` unit test in `test_llm_gateway.py`.
- Verified all 22 pytest tests pass cleanly.

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
