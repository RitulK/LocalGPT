# LocalGPT

## Project Info

LocalGPT is a local-first full-stack application for chatting with Ollama and
other local model providers. The backend uses FastAPI and SQLite; the frontend
uses React and Vite.

## How to Develop

Backend:

```bash
cd backend
venv/bin/python main.py
```

Run all backend tests from the repository root:

```bash
backend/venv/bin/python -m pytest -q
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
  and health endpoints.
- Chat-first Obsidian Local REST API integration with settings, vault search/read,
  model-generated drafts, confirmation, targeted section edits, and gated delete.
- React/Vite frontend with chat, knowledge-base, memory graph, model, and
  settings views.
- Ollama, OpenAI-compatible vLLM, NVIDIA, TinyFish web tools, Chroma RAG, and
  graph-memory integrations.
- P1–P6 implementation is present, including backend layering, provider
  consolidation, typed SSE events, RAG, graph memory, and async PDF ingestion.
- P7-S1 centralized Pydantic settings and P7-S2 structured JSON logging are
  implemented.

## Feature Updates

- **2026-09-11 — P1-S1:** Added `backend/app/{api,services,domain,infrastructure,core}`,
  moved HTTP routes into routers, and reduced `backend/main.py` to an app
  factory and lifecycle wiring.
- **2026-11-24 — Obsidian chat-first integration:** Added Obsidian connection
  settings, a composer tool menu, provider-independent AI proposal generation,
  editable review cards, REST-only search/read/open, full-note chat rendering,
  conditional writes, and confirmed delete support. Implementation lives in
  `backend/app/api/obsidian.py`, `backend/app/services/obsidian_service.py`,
  `frontend/src/components/ObsidianChatTools.jsx`, and `ChatWindow.jsx`.

  Approved behavior: users select an Obsidian tool in the composer and provide
  a normal prompt; the selected model generates Markdown or a typed proposal;
  the proposal is reviewed and edited before confirmation; search and note reads
  use the Obsidian REST API directly. Search results show excerpts, and reading a
  note adds its full Markdown to the chat with an Open in Obsidian button.
  Targeted edits use the heading/section and ETag; replacement and deletion require
  explicit confirmation, with deletion disabled unless enabled in Settings.

## Current Status

Backend and frontend implementation is substantially complete through the graph
memory and live-tool work. P7-S1 and P7-S2 are implemented; P7-S3 rate limiting
and CORS hardening remain incomplete. The Phase 8 Laya implementation is still a
simulation and is not connected to RAG retrieval or automatic memory extraction.
Full validation and feature audit results are tracked in `changelog.md`.

## Next Steps

- Complete P7-S3 by wiring SlowAPI to `/chat` and `/documents` and making CORS
  method and header allowlists explicit.
- Replace the Phase 8 Laya simulation with a real ONNX runtime.
- Integrate Laya with dynamic RAG guarding and preference extraction.
- Expand backend and Playwright coverage to match all implemented features.
