# LocalGPT

## Project Info

LocalGPT is a local-first full-stack application for chatting with Ollama and
other local model providers. The backend uses FastAPI and SQLite; the frontend
uses React and Vite.

## How to Develop

Backend:

```bash
cd backend
../backend/.venv/bin/python main.py
```

Run all backend tests from the repository root:

```bash
backend/.venv/bin/python -m pytest -q
```

Read [`repo.md`](repo.md) before making code changes. The backlog contract is
in [`BACKLOG.md`](BACKLOG.md).

## Rules to Follow

- Follow the workflow in `repo.md`.
- Preserve endpoint behavior unless the active backlog item says otherwise.
- Keep `main.py` focused on application construction.
- Keep API routers thin; place business logic in services.
- Add unit tests for new behavior and run the complete suite after features.
- Record every change in `changelog.md`.

## Built So Far

- FastAPI backend with chat, conversation, document, memory, model, settings,
  health, and router-test endpoints.
- React/Vite frontend.
- Ollama, vLLM, NVIDIA, and RAG integrations.
- P1-S1 backend app layering and route extraction.

## Feature Updates

- **2026-09-11 — P1-S1:** Added `backend/app/{api,services,domain,infrastructure,core}`,
  moved HTTP routes into routers, and reduced `backend/main.py` to an app
  factory and lifecycle wiring.

## Current Status

P1-S1 implementation is complete. The structure and root endpoint have been
validated. Full test results are tracked in `changelog.md`.

## Next Steps

- Mark P1-S1 acceptance criteria complete after the full suite passes.
- Continue with P1-S2, moving chat behavior behind the planned `ChatService`
  interface.
