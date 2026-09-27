# Changelog

All notable repository changes are recorded here, newest first.

## 2026-09-27

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
