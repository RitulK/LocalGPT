# LocalGPT — Development Backlog

_Last updated: 2026-08-22_
_Owner: RitulK · AI assistant: GitHub Copilot_
_Plan reference: see `/memories/session/plan.md` (v4)_

> Single source of truth for the LocalGPT refactor. Stories here are the contract.
> Format is compatible with the **Obsidian Kanban plugin** AND plain GitHub-flavored markdown.
> Status values: `todo` · `in-progress` · `blocked` · `review` · `done` · `dropped`

---

## Phase 1 — Layer the backend

> Goal: split the 470-LOC god-file `main.py` into a layered `app/{api,services,domain,infrastructure}` tree. No behavior change.

---

### [P1-S1] Create the `app/` skeleton and split routes out of `main.py`

- **ID:** P1-S1
- **Status:** todo
- **Phase:** 1
- **Priority:** high
- **Estimate:** M (~2–4 h)
- **Depends on:** —
- **Tags:** #refactor #structure
- **Description:** Empty-skeleton commit. Create `backend/app/{api,services,domain,infrastructure,core}` directories. Move every `@app.*` route handler from `main.py` into its own router file under `app/api/`. Reduce `main.py` to a `create_app()` function that wires middleware, lifespan, and router includes.
- **Acceptance criteria:**
  - [ ] `backend/app/api/` contains `chat.py`, `conversations.py`, `documents.py`, `memories.py`, `models.py`, `settings.py`, `health.py`, `deps.py`
  - [ ] `main.py` is ≤ 60 LOC and contains no `@app.*` route handlers
  - [ ] Every route handler is ≤ 15 LOC
  - [ ] `backend/app/api/` files only import from `app.services.*` and `app.domain.*`, not from each other
  - [ ] Existing Playwright tests pass without modification
- **Out of scope:** No business-logic changes. No new endpoints. No auth.
- **Verification:** `wc -l backend/app/main.py` ≤ 60; `grep -c '^@app\.' backend/app/main.py` = 0; manual smoke test of every endpoint.

---

### [P1-S2] Move chat business logic into `ChatService`

- **ID:** P1-S2
- **Status:** todo
- **Phase:** 1
- **Priority:** high
- **Estimate:** M (~2–4 h)
- **Depends on:** P1-S1
- **Tags:** #refactor #services
- **Description:** Extract the body of `POST /chat` from `main.py` (load history → maybe RAG → maybe memory → invoke → persist) into `app/services/chat_service.py` as `ChatService.stream_chat(...)`. The route handler becomes a thin wrapper that delegates.
- **Acceptance criteria:**
  - [ ] `ChatService` has exactly one public method: `stream_chat(request: ChatRequest, conversation_id: int) -> AsyncIterator[StreamEvent]`
  - [ ] The route handler in `app/api/chat.py` is ≤ 12 LOC
  - [ ] `ChatService` imports nothing from `fastapi` (only from `app.domain`, `app.infrastructure`)
  - [ ] Behavior is identical to today's chat endpoint — verified by manual test
- **Verification:** `git diff` shows zero behavior change; existing chat tests pass.

---

### [P1-S3] Extract repositories for SQL access

- **ID:** P1-S3
- **Status:** todo
- **Phase:** 1
- **Priority:** high
- **Estimate:** M (~2–4 h)
- **Depends on:** P1-S2
- **Tags:** #refactor #database
- **Description:** Wrap raw SQL from `database.py` in thin repository classes: `ConversationRepository`, `MessageRepository`, `DocumentRepository`, `MemoryRepository`, `SettingsRepository`. Each repository owns one table.
- **Acceptance criteria:**
  - [ ] `app/infrastructure/db/repositories.py` (or one file per repo) defines each repo as a class
  - [ ] Each repo method takes a `sqlite3.Connection` parameter (no module-level connection)
  - [ ] Services call repositories instead of `database.*` functions
  - [ ] `database.py` becomes a thin re-export for backward compat OR is deleted entirely
  - [ ] `grep -r "import database" app/services/` returns nothing
- **Verification:** `rg "import database" app/services/` returns nothing; existing CRUD tests pass.

---

## Phase 2 — Replace the providers

> Goal: collapse `OllamaClient` + `VLLMClient` + `NvidiaClient` (~600 LOC) into one `LLMGateway` using `ChatOllama` + `ChatOpenAI`. Drop the `[REASONING]…[/REASONING]` string protocol.

---

### [P2-S1] Build the `LLMGateway` and delete the three clients

- **ID:** P2-S1
- **Status:** todo
- **Phase:** 2
- **Priority:** high
- **Estimate:** M (~2–4 h)
- **Depends on:** P1-S3
- **Tags:** #langchain #providers
- **Description:** Add `langchain-core`, `langchain-ollama`, `langchain-openai` to `requirements.txt`. Create `app/infrastructure/llm/gateway.py` with `LLMGateway` that maps `("ollama", "qwen:4b") → ChatOllama(...)`, `("vllm", "llama-...") → ChatOpenAI(base_url=vllm_url, ...)`, `("nvidia", "nvidia/...") → ChatOpenAI(base_url=nvidia_url, ...)`. Delete `backend/ollama_client.py`, `backend/vllm_client.py`, `backend/nvidia_client.py`. Update `ChatService` to call `LLMGateway` instead of the old clients.
- **Acceptance criteria:**
  - [ ] `backend/{ollama,vllm,nvidia}_client.py` are deleted
  - [ ] `app/infrastructure/llm/gateway.py` ≤ 80 LOC
  - [ ] `LLMGateway.stream_chat(provider, model, messages)` returns `AsyncIterator[StreamEvent]`
  - [ ] Existing manual chat test passes for all three providers
  - [ ] `rg "httpx" app/infrastructure/llm/` returns nothing (LangChain handles HTTP)
- **Verification:** `git diff --stat` shows net deletion of ≥ 500 LOC; streaming behavior is byte-identical for non-reasoning content.

---

### [P2-S2] Provider-name convention and registry

- **ID:** P2-S2
- **Status:** todo
- **Phase:** 2
- **Priority:** high
- **Estimate:** S (~1 h)
- **Depends on:** P2-S1
- **Tags:** #refactor #providers
- **Description:** Introduce `provider:model@host` model-name convention. `LLMGateway.stream_chat` parses the prefix and routes to the correct adapter. Update `ModelCatalogService` to format model names returned by the catalog (Ollama → `ollama:`, vLLM → `openai:`, NVIDIA → `openai:`). Update `ChatService` and `ChatRequest` to use the new format.
- **Acceptance criteria:**
  - [ ] All model names in API responses use the prefix convention
  - [ ] `ChatRequest.model` accepts `provider:model@host` format
  - [ ] `rg "nemotron" app/infrastructure/llm/` returns 0 hits (no more string-sniffing)
  - [ ] `rg '"nvidia/"' app/` returns 0 hits
  - [ ] Frontend dropdown displays names from the new format correctly
- **Verification:** Manual test — pick each provider from the UI; backend routes to correct base URL; streaming works.

---

### [P2-S3] Typed SSE events (no more `[REASONING]` strings)

- **ID:** P2-S3
- **Status:** todo
- **Phase:** 2
- **Priority:** medium
- **Estimate:** S (~1 h)
- **Depends on:** P2-S1
- **Tags:** #refactor #sse #types
- **Description:** Define `StreamEvent` Pydantic model in `app/domain/models.py` as a discriminated union over `metadata | content | reasoning | done | error`. Update `LLMGateway` to yield typed events. For NVIDIA, read `delta.reasoning_content` from `ChatOpenAI` and emit `{type: "reasoning", content: ...}`. Delete the string-parsing branch in `ChatService`.
- **Acceptance criteria:**
  - [ ] `app/domain/models.py` defines `StreamEvent` as a discriminated union
  - [ ] `rg "\[REASONING\]" app/` returns 0 hits
  - [ ] `rg "\[/REASONING\]" app/` returns 0 hits
  - [ ] NVIDIA model's reasoning panel populates without parse errors (manual test)
- **Verification:** Manual streaming test on NVIDIA model; trace one SSE chunk and confirm it's a JSON dict with `type` field, not a delimiter string.

---

## Phase 3 — RAG simplification

> Goal: replace the manual `RAGService.retrieve` with `Chroma.as_retriever`. Same behavior, much less code.

---

### [P3-S1] Wrap Chroma in `ChromaStore` with `as_retriever`

- **ID:** P3-S1
- **Status:** todo
- **Phase:** 3
- **Priority:** high
- **Estimate:** S (~1 h)
- **Depends on:** P2-S2
- **Tags:** #langchain #rag
- **Description:** Add `langchain-chroma` to requirements. Create `app/infrastructure/vector/chroma_store.py` with `ChromaStore` class. Move the Chroma initialization from `RAGService` into this class. Expose `as_retriever(document_ids: list[int], k: int) -> Retriever`.
- **Acceptance criteria:**
  - [ ] `app/infrastructure/vector/chroma_store.py` ≤ 80 LOC
  - [ ] `ChromaStore.as_retriever(document_ids=[1,2], k=5)` returns a retriever filtered to those document IDs
  - [ ] `pypdf` PDF parsing stays in `RAGService` (no LangChain loader)
- **Verification:** `python -c "from app.infrastructure.vector.chroma_store import ChromaStore; ..."` succeeds; upload + query round-trip works.

---

### [P3-S2] Replace `RAGService.retrieve` with the retriever

- **ID:** P3-S2
- **Status:** todo
- **Phase:** 3
- **Priority:** high
- **Estimate:** S (~1 h)
- **Depends on:** P3-S1
- **Tags:** #refactor #rag
- **Description:** Replace the body of `RAGService.retrieve(prompt, document_ids, ...)` with one call: `await chroma_store.as_retriever(...).ainvoke(prompt)`. Update `ChatService` to consume the new return shape (list of LangChain `Document` instead of list of dict).
- **Acceptance criteria:**
  - [ ] `RAGService.retrieve` ≤ 10 LOC
  - [ ] Chat with RAG returns the same citations and snippets as today (manual test)
  - [ ] `rg "self.get_collection\(\).query" app/` returns 0 hits
- **Verification:** Upload a PDF, ask a question, get the same answer with the same source list as before refactor.

---

## Phase 4 — Remove the router

> Goal: delete the `ModelRouter` entirely. User always picks the model. `use_router` flag, `/router/test`, capability dict all gone.

---

### [P4-S1] Delete the model router and clean up

- **ID:** P4-S1
- **Status:** todo
- **Phase:** 4
- **Priority:** high
- **Estimate:** S (~1 h)
- **Depends on:** P1-S3
- **Tags:** #cleanup #router
- **Description:** Delete `backend/router.py`. Remove `ModelRouter`, `QuestionType`, `MODEL_CAPABILITIES`, all keyword/regex lists. Remove `use_router` field from `ChatRequest`. Remove `/router/test` endpoint. Remove `default_general_model`, `default_coding_model`, `default_reasoning_model`, `router_enabled`, `router_models` from settings.
- **Acceptance criteria:**
  - [ ] `backend/router.py` deleted
  - [ ] `rg "use_router" app/` returns 0 hits
  - [ ] `rg "MODEL_CAPABILITIES" app/` returns 0 hits
  - [ ] `rg "QuestionType" app/` returns 0 hits
  - [ ] Frontend "auto-route" toggle is removed from `ChatWindow.jsx` and `Sidebar.jsx`
  - [ ] Settings UI no longer shows the routing defaults
- **Verification:** Manual test — chat works with a model selected from the dropdown; no router-related code paths remain.

---

## Phase 5 — Memory that works

> Goal: make the dead `memories` table actually influence chat output.

---

### [P5-S1] Memory embeddings on create

- **ID:** P5-S1
- **Status:** todo
- **Phase:** 5
- **Priority:** medium
- **Estimate:** M (~2–4 h)
- **Depends on:** P3-S1
- **Tags:** #rag #memory
- **Description:** Add a `localgpt_memories` Chroma collection. When a memory is created via `POST /memories`, embed it (using `OllamaEmbeddings` from LangChain) and store the embedding alongside the metadata `{memory_id, kind, source}`. When a memory is deleted, remove the matching Chroma entry.
- **Acceptance criteria:**
  - [ ] `ChromaStore` exposes `add_memory(memory_id, content, kind, source)` and `delete_memory(memory_id)`
  - [ ] `POST /memories` returns within 500ms; embedding runs synchronously but is fast for short text
  - [ ] `DELETE /memories/{id}` removes both the SQL row and the Chroma entry
  - [ ] `rg "embedding" app/infrastructure/vector/chroma_store.py` shows the memory collection is separate from the document collection
- **Verification:** Create a memory, delete it, query Chroma directly — the entry is gone.

---

### [P5-S2] Inject top-k memories into the chat prompt

- **ID:** P5-S2
- **Status:** todo
- **Phase:** 5
- **Priority:** medium
- **Estimate:** S (~1 h)
- **Depends on:** P5-S1
- **Tags:** #rag #memory
- **Description:** Add `MemoryService.retrieve_relevant(prompt, k=3) -> list[Memory]`. In `ChatService.stream_chat`, after RAG retrieval and before LLM invocation, call this and prepend a system message listing the relevant memories.
- **Acceptance criteria:**
  - [ ] `MemoryService.retrieve_relevant` ≤ 25 LOC
  - [ ] The injected memory block has the format: `"Relevant notes you have saved:\n- [memory 1]\n- [memory 2]\n- [memory 3]"`
  - [ ] When no memories match, no system message is injected (no empty block)
  - [ ] The `kind` and `source` parameters in the injection are filterable via settings (default: include all)
- **Verification:** Create a memory "User prefers concise answers under 3 paragraphs"; ask "explain async/await"; confirm response is shorter than without the memory.

---

## Phase 6 — Async ingestion

> Goal: PDF uploads return immediately. Background task does the heavy lifting.

---

### [P6-S1] BackgroundTasks for PDF ingestion

- **ID:** P6-S1
- **Status:** todo
- **Phase:** 6
- **Priority:** high
- **Estimate:** S (~1 h)
- **Depends on:** P1-S3
- **Tags:** #async #ingest
- **Description:** `POST /documents` should return within 500ms with `status="pending"`. The actual extract → chunk → embed pipeline runs in a FastAPI `BackgroundTasks` callback. Frontend polls `GET /documents/{id}` until `status="ready"`.
- **Acceptance criteria:**
  - [ ] `POST /documents` returns in < 500ms with `{id, status: "pending", ...}`
  - [ ] Within 10 seconds (for a typical PDF), `GET /documents/{id}` returns `status="ready"`
  - [ ] `rg "BackgroundTasks" app/api/documents.py` shows the dependency is injected
  - [ ] Frontend polls correctly (no UI freeze)
- **Out of scope:** ARQ / Redis. If the process crashes mid-ingest, the job is lost — flag this with a TODO comment.
- **Verification:** Upload a 50-page PDF; POST returns < 500ms; status flips to `ready` within 10s; the doc is queryable in a chat.

---

## Phase 7 — Hygiene

> Goal: replace scattered config and bare prints with proper config + structured logs. Lock CORS. Add rate limits.

---

### [P7-S1] `pydantic-settings` for configuration

- **ID:** P7-S1
- **Status:** todo
- **Phase:** 7
- **Priority:** medium
- **Estimate:** S (~1 h)
- **Depends on:** P1-S1
- **Tags:** #config
- **Description:** Replace scattered `os.getenv(...)` calls in clients and `main.py` with a single `Settings(BaseSettings)` class in `app/core/config.py`. Add `.env.example` documenting every variable. Include `DATABASE_URL` (default `sqlite:///./localgpt.db`) so a Postgres swap is a one-line change later.
- **Acceptance criteria:**
  - [ ] `app/core/config.py` defines `Settings` with all current config
  - [ ] `.env.example` lists every variable with a comment
  - [ ] `rg "os.getenv" app/` returns 0 hits
  - [ ] Adding a new setting requires editing only `Settings`
- **Verification:** `python -c "from app.core.config import Settings; print(Settings().model_dump())"` succeeds without env vars.

---

### [P7-S2] `structlog` for JSON logs

- **ID:** P7-S2
- **Status:** todo
- **Phase:** 7
- **Priority:** low
- **Estimate:** S (~1 h)
- **Depends on:** P7-S1
- **Tags:** #logging
- **Description:** Configure `structlog` in `app/core/logging.py`. Replace `print(...)` and `logging.basicConfig` in `main.py` and clients with structured log calls.
- **Acceptance criteria:**
  - [ ] `app/core/logging.py` configures JSON output to stdout
  - [ ] `rg "^print\(" app/` returns 0 hits
  - [ ] Logs include request_id and latency
- **Verification:** Hit any endpoint; log output is JSON, one line per event.

---

### [P7-S3] Lock CORS and add rate limits

- **ID:** P7-S3
- **Status:** todo
- **Phase:** 7
- **Priority:** low
- **Estimate:** S (~1 h)
- **Depends on:** P1-S1
- **Tags:** #security #cors
- **Description:** Lock CORS to known origins (no wildcards). Add `slowapi` rate limits: 60 req/min on `/chat`, 30 req/min on `/documents`.
- **Acceptance criteria:**
  - [ ] `allow_origins` lists exactly `localhost:5173`, `localhost:5174`, `localhost:3000`
  - [ ] `allow_methods` and `allow_headers` are explicit lists, not `["*"]`
  - [ ] 61st `/chat` request in a minute returns HTTP 429
  - [ ] `app/main.py` shows the `slowapi` limiter wiring
- **Verification:** `curl` test for rate limiting; check response headers for CORS lockdown.

---

## Phase Summary

| Phase | Stories | Status |
|---|---|---|
| 1 — Layer the backend | P1-S1, P1-S2, P1-S3 | not started |
| 2 — Replace providers | P2-S1, P2-S2, P2-S3 | not started |
| 3 — RAG simplification | P3-S1, P3-S2 | not started |
| 4 — Remove router | P4-S1 | not started |
| 5 — Memory works | P5-S1, P5-S2 | not started |
| 6 — Async ingestion | P6-S1 | not started |
| 7 — Hygiene | P7-S1, P7-S2, P7-S3 | not started |

**Total: 13 stories across 7 phases.**

---

## How to use this file

### Updating status

Edit the `**Status:**` line. The AI reads this at the start of each session.

```markdown
- **Status:** todo          ← start here
- **Status:** in-progress   ← you're working on it
- **Status:** blocked       ← stuck, see Notes
- **Status:** review        ← code done, awaiting review
- **Status:** done          ← acceptance criteria all checked
- **Status:** dropped       ← no longer needed
```

### Tracking acceptance criteria

Each story has a checklist. Tick as you complete each one:

```markdown
- [ ] First thing
- [x] Second thing       ← done
- [ ] Third thing
```

The `[x]` checkboxes are how you (and the AI) know what partial progress has happened.

### Reading in VS Code

See `docs/backlog-workflow.md` for the rendering guide.

---

## Notes

- _2026-08-22:_ Backlog created from plan v4. All 13 stories approved.
