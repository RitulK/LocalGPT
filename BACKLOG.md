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
- **Status:** completed
- **Phase:** 1
- **Priority:** high
- **Estimate:** M (~2–4 h)
- **Depends on:** —
- **Tags:** #refactor #structure
- **Description:** Empty-skeleton commit. Create `backend/app/{api,services,domain,infrastructure,core}` directories. Move every `@app.*` route handler from `main.py` into its own router file under `app/api/`. Reduce `main.py` to a `create_app()` function that wires middleware, lifespan, and router includes.
- **Acceptance criteria:**
  - [x] `backend/app/api/` contains `chat.py`, `conversations.py`, `documents.py`, `memories.py`, `models.py`, `settings.py`, `health.py`, `deps.py`
  - [x] `main.py` is ≤ 60 LOC and contains no `@app.*` route handlers
  - [x] Every route handler is ≤ 15 LOC
  - [x] `backend/app/api/` files only import from `app.services.*` and `app.domain.*`, not from each other
  - [x] Existing Playwright tests pass without modification
- **Out of scope:** No business-logic changes. No new endpoints. No auth.
- **Verification:** `wc -l backend/app/main.py` ≤ 60; `grep -c '^@app\.' backend/app/main.py` = 0; manual smoke test of every endpoint.

---

### [P1-S2] Move chat business logic into `ChatService`

- **ID:** P1-S2
- **Status:** completed
- **Phase:** 1
- **Priority:** high
- **Estimate:** M (~2–4 h)
- **Depends on:** P1-S1
- **Tags:** #refactor #services
- **Description:** Extract the body of `POST /chat` from `main.py` (load history → maybe RAG → maybe memory → invoke → persist) into `app/services/chat_service.py` as `ChatService.stream_chat(...)`. The route handler becomes a thin wrapper that delegates.
- **Acceptance criteria:**
  - [x] `ChatService` has exactly one public method: `stream_chat(request: ChatRequest, conversation_id: int) -> AsyncIterator[StreamEvent]`
  - [x] The route handler in `app/api/chat.py` is ≤ 12 LOC
  - [x] `ChatService` imports nothing from `fastapi` (only from `app.domain`, `app.infrastructure`)
  - [x] Behavior is identical to today's chat endpoint — verified by manual test
- **Verification:** `git diff` shows zero behavior change; existing chat tests pass.

---

### [P1-S3] Extract repositories for SQL access

- **ID:** P1-S3
- **Status:** completed
- **Phase:** 1
- **Priority:** high
- **Estimate:** M (~2–4 h)
- **Depends on:** P1-S2
- **Tags:** #refactor #database
- **Description:** Wrap raw SQL from `database.py` in thin repository classes: `ConversationRepository`, `MessageRepository`, `DocumentRepository`, `MemoryRepository`, `SettingsRepository`. Each repository owns one table.
- **Acceptance criteria:**
  - [x] `app/infrastructure/db/repositories.py` (or one file per repo) defines each repo as a class
  - [x] Each repo method takes a `sqlite3.Connection` parameter (no module-level connection)
  - [x] Services call repositories instead of `database.*` functions
  - [x] `database.py` becomes a thin re-export for backward compat OR is deleted entirely
  - [x] `grep -r "import database" app/services/` returns nothing
- **Verification:** `rg "import database" app/services/` returns nothing; existing CRUD tests pass.

---

## Phase 2 — Replace the providers

> Goal: collapse `OllamaClient` + `VLLMClient` + `NvidiaClient` (~600 LOC) into one `LLMGateway` using `ChatOllama` + `ChatOpenAI`. Drop the `[REASONING]…[/REASONING]` string protocol.

---

### [P2-S1] Build the `LLMGateway` and delete the three clients

- **ID:** P2-S1
- **Status:** completed
- **Phase:** 2
- **Priority:** high
- **Estimate:** M (~2–4 h)
- **Depends on:** P1-S3
- **Tags:** #langchain #providers
- **Description:** Add `langchain-core`, `langchain-ollama`, `langchain-openai` to `requirements.txt`. Create `app/infrastructure/llm/gateway.py` with `LLMGateway` that maps `("ollama", "qwen:4b") → ChatOllama(...)`, `("vllm", "llama-...") → ChatOpenAI(base_url=vllm_url, ...)`, `("nvidia", "nvidia/...") → ChatOpenAI(base_url=nvidia_url, ...)`. Delete `backend/ollama_client.py`, `backend/vllm_client.py`, `backend/nvidia_client.py`. Update `ChatService` to call `LLMGateway` instead of the old clients.
- **Acceptance criteria:**
  - [x] `backend/{ollama,vllm,nvidia}_client.py` are deleted
  - [x] `app/infrastructure/llm/gateway.py` ≤ 80 LOC
  - [x] `LLMGateway.stream_chat(provider, model, messages)` returns `AsyncIterator[StreamEvent]`
  - [x] Existing manual chat test passes for all three providers
  - [x] `rg "httpx" app/infrastructure/llm/` returns nothing (LangChain handles HTTP)
- **Verification:** `git diff --stat` shows net deletion of ≥ 500 LOC; streaming behavior is byte-identical for non-reasoning content.

---

### [P2-S2] Provider-name convention and registry

- **ID:** P2-S2
- **Status:** completed
- **Phase:** 2
- **Priority:** high
- **Estimate:** S (~1 h)
- **Depends on:** P2-S1
- **Tags:** #refactor #providers
- **Description:** Introduce `provider:model@host` model-name convention. `LLMGateway.stream_chat` parses the prefix and routes to the correct adapter. Update `ModelCatalogService` to format model names returned by the catalog (Ollama → `ollama:`, vLLM → `openai:`, NVIDIA → `openai:`). Update `ChatService` and `ChatRequest` to use the new format.
- **Acceptance criteria:**
  - [x] All model names in API responses use the prefix convention
  - [x] `ChatRequest.model` accepts `provider:model@host` format
  - [x] `rg "nemotron" app/infrastructure/llm/` returns 0 hits (no more string-sniffing)
  - [x] `rg '"nvidia/"' app/` returns 0 hits
  - [x] Frontend dropdown displays names from the new format correctly
- **Verification:** Manual test — pick each provider from the UI; backend routes to correct base URL; streaming works.

---

### [P2-S3] Typed SSE events (no more `[REASONING]` strings)

- **ID:** P2-S3
- **Status:** completed
- **Phase:** 2
- **Priority:** medium
- **Estimate:** S (~1 h)
- **Depends on:** P2-S1
- **Tags:** #refactor #sse #types
- **Description:** Define `StreamEvent` Pydantic model in `app/domain/models.py` as a discriminated union over `metadata | content | reasoning | done | error`. Update `LLMGateway` to yield typed events. For NVIDIA, read `delta.reasoning_content` from `ChatOpenAI` and emit `{type: "reasoning", content: ...}`. Delete the string-parsing branch in `ChatService`.
- **Acceptance criteria:**
  - [x] `app/domain/models.py` defines `StreamEvent` as a discriminated union
  - [x] `rg "\[REASONING\]" app/` returns 0 hits
  - [x] `rg "\[/REASONING\]" app/` returns 0 hits
  - [x] NVIDIA model's reasoning panel populates without parse errors (manual test)
- **Verification:** Manual streaming test on NVIDIA model; trace one SSE chunk and confirm it's a JSON dict with `type` field, not a delimiter string.

---

## Phase 3 — RAG simplification

> Goal: replace the manual `RAGService.retrieve` with `Chroma.as_retriever`. Same behavior, much less code.

---

### [P3-S1] Wrap Chroma in `ChromaStore` with `as_retriever`

- **ID:** P3-S1
- **Status:** completed
- **Phase:** 3
- **Priority:** high
- **Estimate:** S (~1 h)
- **Depends on:** P2-S2
- **Tags:** #langchain #rag
- **Description:** Add `langchain-chroma` to requirements. Create `app/infrastructure/vector/chroma_store.py` with `ChromaStore` class. Move the Chroma initialization from `RAGService` into this class. Expose `as_retriever(document_ids: list[int], k: int) -> Retriever`.
- **Acceptance criteria:**
  - [x] `app/infrastructure/vector/chroma_store.py` ≤ 80 LOC
  - [x] `ChromaStore.as_retriever(document_ids=[1,2], k=5)` returns a retriever filtered to those document IDs
  - [x] `pypdf` PDF parsing stays in `RAGService` (no LangChain loader)
- **Verification:** `python -c "from app.infrastructure.vector.chroma_store import ChromaStore; ..."` succeeds; upload + query round-trip works.

---

### [P3-S2] Replace `RAGService.retrieve` with the retriever

- **ID:** P3-S2
- **Status:** completed
- **Phase:** 3
- **Priority:** high
- **Estimate:** S (~1 h)
- **Depends on:** P3-S1
- **Tags:** #refactor #rag
- **Description:** Replace the body of `RAGService.retrieve(prompt, document_ids, ...)` with one call: `await chroma_store.as_retriever(...).ainvoke(prompt)`. Update `ChatService` to consume the new return shape (list of LangChain `Document` instead of list of dict).
- **Acceptance criteria:**
  - [x] `RAGService.retrieve` ≤ 10 LOC
  - [x] Chat with RAG returns the same citations and snippets as today (manual test)
  - [x] `rg "self.get_collection\(\).query" app/` returns 0 hits
- **Verification:** Upload a PDF, ask a question, get the same answer with the same source list as before refactor.

---

## Phase 4 — Remove the router

> Goal: delete the `ModelRouter` entirely. User always picks the model. `use_router` flag, `/router/test`, capability dict all gone.

---

### [P4-S1] Delete the model router and clean up

- **ID:** P4-S1
- **Status:** completed
- **Phase:** 4
- **Priority:** high
- **Estimate:** S (~1 h)
- **Depends on:** P1-S3
- **Tags:** #cleanup #router
- **Description:** Delete `backend/router.py`. Remove `ModelRouter`, `QuestionType`, `MODEL_CAPABILITIES`, all keyword/regex lists. Remove `use_router` field from `ChatRequest`. Remove `/router/test` endpoint. Remove `default_general_model`, `default_coding_model`, `default_reasoning_model`, `router_enabled`, `router_models` from settings.
- **Acceptance criteria:**
  - [x] `backend/router.py` deleted
  - [x] `rg "use_router" app/` returns 0 hits
  - [x] `rg "MODEL_CAPABILITIES" app/` returns 0 hits
  - [x] `rg "QuestionType" app/` returns 0 hits
  - [x] Frontend "auto-route" toggle is removed from `ChatWindow.jsx` and `Sidebar.jsx`
  - [x] Settings UI no longer shows the routing defaults
- **Verification:** Manual test — chat works with a model selected from the dropdown; no router-related code paths remain.

---

## Phase 5 — Graph Memory & Context Plugins

> Goal: Build an interconnected knowledge graph of user memories (messages and thread snapshots). Users capture insights from any chat, visualize linked concepts, and plug memories dynamically into new conversations as rich graph context.

---

### [P5-S1] Graph Memory Backend & LangGraph Context Compiler

- **ID:** P5-S1
- **Status:** completed
- **Phase:** 5
- **Priority:** high
- **Estimate:** M (~2–3 h)
- **Depends on:** P1-S3
- **Tags:** #graph #memory #langgraph
- **Description:** Implement SQLite graph storage (`memory_nodes` and `memory_edges` tables) and a LangGraph traversal compiler. Support saving individual messages as nodes, and saving thread snapshots (conversations up to message $N$) where sequential messages are automatically linked with directed `follows` edges. Provide APIs for creating custom `relates_to` conceptual links, querying subgraphs, and compiling selected nodes + neighbors into structured chat context.
- **Acceptance criteria:**
  - [x] Tables `memory_nodes` (`id`, `node_type`, `title`, `content`, `source_conversation_id`, `source_message_id`, `metadata`, `created_at`) and `memory_edges` (`id`, `source_id`, `target_id`, `relation`, `metadata`, `created_at`) created in SQLite
  - [x] `POST /memories/capture/message` captures an individual message into `memory_nodes`
  - [x] `POST /memories/capture/thread` captures all messages up to target message ID and automatically generates sequential `follows` edges between consecutive turns
  - [x] `POST /memories/edges` creates custom `relates_to` relationships between any two nodes
  - [x] `GET /memories/graph` returns the full graph structure (nodes + edges) with node_type and conversation filters
  - [x] `DELETE /memories/{id}` cascades to remove the node and all connected edges
  - [x] `MemoryGraphService.compile_context(node_ids, depth=1)` traverses selected nodes and 1-hop connected neighbors using LangGraph/graph traversal, producing a formatted markdown context block
- **Verification:** Unit test capturing a 4-message thread snapshot; verify 4 nodes and 3 `follows` edges created in SQLite; verify `compile_context` resolves connected context.

---

### [P5-S2] Chat Save Actions & Plug-and-Play Memory Context

- **ID:** P5-S2
- **Status:** completed
- **Phase:** 5
- **Priority:** high
- **Estimate:** M (~2–3 h)
- **Depends on:** P5-S1
- **Tags:** #chat #ui #memory
- **Description:** Add intuitive memory capture actions directly onto chat message bubbles, and enable plug-and-play memory context injection in the chat composer so users can easily select and attach memory nodes to any active conversation.
- **Acceptance criteria:**
  - [x] Assistant message bubbles in `ChatWindow.jsx` have hover action menu with "Save message to Memory" and "Save thread up to here"
  - [x] Clicking a save action invokes capture API and displays a success toast notification
  - [x] `ChatWindow.jsx` composer adds a "Memory" button next to "Knowledge" displaying an active memory count badge
  - [x] Clicking "Memory" opens a selector popover to search, preview, and toggle memory nodes for the conversation
  - [x] Selected memories render as dismissible chips above the message input
  - [x] `ChatRequest` schema and `ChatService.stream_chat` accept `memory_node_ids: Optional[List[str]]` and prepend compiled graph context before conversation history
- **Verification:** Save an assistant response to memory from chat; start a new conversation and toggle that memory on; ask a question referencing the saved note; verify LLM output reflects the injected memory context.

---

### [P5-S3] Interactive Memory Graph Visualizer & Linker

- **ID:** P5-S3
- **Status:** completed
- **Phase:** 5
- **Priority:** medium
- **Estimate:** M (~2–4 h)
- **Depends on:** P5-S1
- **Tags:** #visualizer #canvas #graph #ui
- **Description:** Build an interactive force-directed graph visualizer in the frontend (Memory view/tab) to render memory nodes and edges. Users can pan/zoom, drag nodes, inspect memory content, and interactively connect disparate memories with `relates_to` conceptual links.
- **Acceptance criteria:**
  - [x] "Memory Graph" navigation tab available in `Sidebar.jsx`
  - [x] Force-directed graph rendered via Canvas/SVG with distinct styling for node types (`message`, `thread_snapshot`, `preference`) and edge types (`follows` vs `relates_to`)
  - [x] Clicking any node opens an inspection drawer showing title, full markdown content, creation timestamp, and connected edges
  - [x] Visual linking tool: select source node and target node in visualizer to persist a `relates_to` edge via `POST /memories/edges`
  - [x] Ability to delete nodes or edges directly from the visualizer with immediate canvas refresh
- **Verification:** Open Memory tab, visually drag nodes, connect two separate thread memories with a `relates_to` link; reload page and confirm edge persists in graph layout.

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

## Phase 8 — System 1 Decision Intelligence (Laya Engine)

> Goal: Introduce local, zero-token, non-autoregressive decision models (Laya ModernBERT-large ONNX, ~20ms) for high-speed gating, classification, and automatic memory extraction without LLM generation overhead.

---

### [P8-S1] Local Laya ONNX runtime & Decision Service

- **ID:** P8-S1
- **Status:** todo
- **Phase:** 8
- **Priority:** high
- **Estimate:** M (~2–3 h)
- **Depends on:** P1-S1
- **Tags:** #laya #system1 #onnx
- **Description:** Implement a local, lightweight Decision Service running Laya (ModernBERT-large non-autoregressive encoder) via `onnxruntime`. Expose typed single-pass inference (`Noul`, `Choice`, `Score`) with sub-30ms latency on local hardware.
- **Acceptance criteria:**
  - [ ] `onnxruntime` dependency added to `backend/requirements.txt`
  - [ ] `LayaDecisionService` implemented in `backend/app/infrastructure/decision/laya_service.py`
  - [ ] Exposes `predict_noul(prompt: str, question: str) -> float` (calibrated binary probability 0.0 to 1.0)
  - [ ] Exposes `predict_choice(prompt: str, categories: List[str]) -> Dict[str, float]`
  - [ ] Single forward pass completes in < 40ms on CPU or Apple Silicon without autoregressive token generation
- **Verification:** Unit test benchmarking `predict_noul` on test prompts; verify execution takes < 40ms and returns float between 0.0 and 1.0.

---

### [P8-S2] Dynamic RAG Retrieval Guard

- **ID:** P8-S2
- **Status:** todo
- **Phase:** 8
- **Priority:** medium
- **Estimate:** S (~1 h)
- **Depends on:** P8-S1, P3-S2
- **Tags:** #rag #guard #laya
- **Description:** Use Laya's `Noul` decision to dynamically guard Chroma vector retrieval. When `use_rag=true`, evaluate whether the prompt actually requires document context; skip Chroma search on greetings, follow-ups, or general knowledge to eliminate context pollution and reduce latency.
- **Acceptance criteria:**
  - [ ] In `ChatService.stream_chat`, when `request.use_rag` is true, invoke `LayaDecisionService.predict_noul(prompt, "Does this prompt require searching uploaded knowledge documents?")`
  - [ ] If probability < 0.45 (e.g. "Hi", "Thanks", "Write a hello world script"), Chroma retrieval is skipped
  - [ ] If skipped, `MetadataEvent.rag_used` is set to `False` and `MetadataEvent.rag_bypassed` is set to `True`
  - [ ] Chat UI displays a subtle indicator when RAG retrieval is bypassed for conversational inputs
- **Verification:** Send "Hello there" with RAG enabled; verify retrieval is skipped with 0ms Chroma delay. Send "What is the policy in Section 2 of handbook.pdf"; verify RAG triggers normally.

---

### [P8-S3] Automatic Memory & Rule Extraction into Memory Graph

- **ID:** P8-S3
- **Status:** todo
- **Phase:** 8
- **Priority:** medium
- **Estimate:** M (~2 h)
- **Depends on:** P8-S1, P5-S1
- **Tags:** #memory #laya #extraction
- **Description:** Automatically detect when a user prompt contains persistent preferences, coding guidelines, or project rules using Laya, and automatically create a `preference` node linked into the Memory Graph.
- **Acceptance criteria:**
  - [ ] Post-prompt hook in `ChatService` evaluates user message with Laya: `predict_noul(prompt, "Does this message declare a persistent rule, instruction, or preference for future conversations?")`
  - [ ] When confidence exceeds threshold (> 0.8), automatically create a node in `memory_nodes` with `node_type="preference"`
  - [ ] An edge is created automatically linking the preference node to the source conversation
  - [ ] Frontend displays a non-intrusive toast: "Captured preference into Memory Graph: [Rule]" with a 1-click "Undo" button
- **Verification:** Send prompt "Always write responses in bullet points and format code in TypeScript"; verify a new node is automatically added to `memory_nodes` with `node_type="preference"`.

---

## Phase Summary

| Phase | Stories | Status |
|---|---|---|
| 1 — Layer the backend | P1-S1, P1-S2, P1-S3 | Done |
| 2 — Replace providers | P2-S1, P2-S2, P2-S3 | Done |
| 3 — RAG simplification | P3-S1, P3-S2 | Done |
| 4 — Remove router | P4-S1 | Done |
| 5 — Graph Memory & Context Plugins | P5-S1, P5-S2, P5-S3 | Done |
| 6 — Async ingestion | P6-S1 | not started |
| 7 — Hygiene | P7-S1, P7-S2, P7-S3 | not started |
| 8 — System 1 Decision Intelligence (Laya) | P8-S1, P8-S2, P8-S3 | not started |

**Total: 17 stories across 8 phases.**

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
