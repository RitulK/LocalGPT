# LocalGPT Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                         │
│                   http://localhost:5173                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/SSE
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │              │  │              │  │              │     │
│  │  ChatWindow  │  │   Sidebar    │  │  Settings    │     │
│  │              │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │              │  │              │  │              │     │
│  │MessageBubble │  │ModelSelector │  │ModelManage   │     │
│  │              │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  Features:                                                  │
│  • Streaming response display                              │
│  • Markdown rendering                                       │
│  • Code syntax highlighting                                 │
│  • Conversation management                                  │
│  • Dark mode UI                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ REST API / Server-Sent Events
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                        │
│                  http://localhost:8000                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              API ENDPOINTS                          │   │
│  │                                                     │   │
│  │  GET  /models          → List installed models     │   │
│  │  POST /chat            → Stream chat responses     │   │
│  │  GET  /health          → Check Ollama status       │   │
│  │  GET  /settings        → Get configuration         │   │
│  │  POST /settings        → Update configuration      │   │
│  │  POST /router/test     → Test routing logic        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────┐                                       │
│  │  ModelRouter    │  ← Intelligent routing logic          │
│  │                 │    • Keyword detection                 │
│  │  - Analyzes     │    • Code block detection              │
│  │    prompts      │    • Length analysis                   │
│  │  - Selects      │    • Custom rules                      │
│  │    best model   │                                        │
│  └─────────────────┘                                       │
│                                                             │
│  ┌─────────────────┐                                       │
│  │  OllamaClient   │  ← HTTP client for Ollama             │
│  │                 │    • Async requests                    │
│  │  - Fetches      │    • Streaming support                 │
│  │    models       │    • Error handling                    │
│  │  - Streams      │                                        │
│  │    responses    │                                        │
│  └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     OLLAMA SERVER                           │
│                http://localhost:11434                       │
│                                                             │
│  Endpoints used:                                            │
│  • GET  /api/tags       → List models                      │
│  • POST /api/chat       → Generate responses               │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │              │  │              │  │              │     │
│  │   llama3.2   │  │qwen2.5-coder │  │   mistral    │     │
│  │              │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  (Your locally installed LLM models)                        │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Sends Message

```
User Input → ChatWindow → API Request → Backend /chat endpoint
                                              │
                                              ▼
                                        Router analyzes prompt
                                              │
                                              ▼
                                        Selects best model
                                              │
                                              ▼
                                        OllamaClient
                                              │
                                              ▼
                                        Ollama Server
                                              │
                                              ▼
                                        Selected LLM Model
```

### 2. Streaming Response

```
LLM generates tokens ────────► Ollama Server
                                     │
                                     │ Stream
                                     ▼
                              OllamaClient
                                     │
                                     │ SSE (Server-Sent Events)
                                     ▼
                              FastAPI /chat
                                     │
                                     │ SSE stream
                                     ▼
                              Frontend ChatWindow
                                     │
                                     │ Real-time update
                                     ▼
                              MessageBubble component
                                     │
                                     ▼
                              User sees response token-by-token
```

## Router Decision Flow

```
                    ┌──────────────────┐
                    │   User Prompt    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Use Router?    │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
           YES│                             │NO
              │                             │
              ▼                             ▼
    ┌──────────────────┐          ┌──────────────────┐
    │  Analyze Prompt  │          │  Use Selected    │
    │                  │          │     Model        │
    │ • Keywords       │          └──────────────────┘
    │ • Code blocks    │
    │ • Length         │
    │ • Custom rules   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Match Found?     │
    └────────┬─────────┘
             │
    ┌────────┴────────┐
    │                 │
Coding│            Reasoning│
    │                 │
    ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Coding    │  │  Reasoning  │  │   General   │
│    Model    │  │    Model    │  │    Model    │
│             │  │             │  │             │
│qwen2.5-coder│  │  llama3.2   │  │  llama3.2   │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Component Hierarchy

```
App
├── Sidebar
│   ├── Tab Navigation (Chat, Models, Settings)
│   ├── ModelSelector
│   │   └── Dropdown with auto-router option
│   └── Conversation List
│       └── Individual conversation items
│
└── Main Content Area
    ├── ChatWindow (when Chat tab active)
    │   ├── Messages Area
    │   │   └── MessageBubble (multiple)
    │   │       ├── User message
    │   │       └── Assistant message
    │   │           ├── Model indicator
    │   │           ├── Markdown content
    │   │           ├── Code blocks (highlighted)
    │   │           └── Copy button
    │   └── Input Area
    │       ├── Textarea
    │       ├── Send button
    │       └── Clear chat button
    │
    ├── SettingsPanel (when Settings tab active)
    │   ├── Router toggle
    │   ├── Default model selectors
    │   │   ├── General model
    │   │   ├── Coding model
    │   │   └── Reasoning model
    │   └── Save/Reset buttons
    │
    └── ModelManagement (when Models tab active)
        ├── Stats cards
        │   ├── Total models
        │   ├── Active model
        │   └── Total size
        └── Model list
            └── Model cards (multiple)
                ├── Name
                ├── Size
                ├── Modified date
                └── Status indicator
```

## Technology Stack Details

### Frontend
- **React 18.2** - UI framework
- **Vite 5.0** - Build tool and dev server
- **Tailwind CSS 3.4** - Styling
- **react-markdown 9.0** - Markdown rendering
- **react-syntax-highlighter 15.5** - Code highlighting
- **Lucide React** - Icons

### Backend
- **FastAPI 0.109** - Web framework
- **Uvicorn 0.27** - ASGI server
- **httpx 0.26** - Async HTTP client
- **Pydantic 2.5** - Data validation

### Communication
- **REST API** - For standard requests
- **SSE (Server-Sent Events)** - For streaming responses
- **JSON** - Data format

### Local AI
- **Ollama** - LLM server (localhost:11434)
- **Various models** - llama3.2, qwen2.5-coder, etc.

## File Organization

```
Frontend Components:
└── src/
    ├── App.jsx                    # Main app with state management
    ├── components/
    │   ├── ChatWindow.jsx         # Chat UI + streaming logic
    │   ├── MessageBubble.jsx      # Individual message with markdown
    │   ├── Sidebar.jsx            # Navigation + model selector
    │   ├── SettingsPanel.jsx      # Configuration UI
    │   └── ModelManagement.jsx    # Model list and stats
    └── index.css                  # Global styles + Tailwind

Backend Modules:
└── backend/
    ├── main.py                    # FastAPI app + endpoints
    ├── router.py                  # Routing logic
    └── ollama_client.py           # Ollama API client
```

## Key Features by Component

### ChatWindow
- Streaming response handling
- Conversation state management
- Auto-scroll to bottom
- Error handling and display
- Keyboard shortcuts

### MessageBubble
- Markdown rendering
- Syntax highlighting for code
- Copy to clipboard functionality
- Timestamp display
- Loading states

### ModelRouter
- Keyword-based routing
- Code detection
- Length analysis
- Customizable rules
- Fallback logic

### OllamaClient
- Async HTTP requests
- SSE streaming
- Error handling
- Connection checking
- Model listing

## Security Considerations

- ✅ Local-only operation (no external APIs)
- ✅ CORS configured for localhost only
- ✅ No sensitive data storage
- ✅ All data stays on your machine
- ✅ No authentication needed (local use)

## Performance Optimizations

- **Streaming responses** - No waiting for complete generation
- **Async operations** - Non-blocking backend
- **Component memoization** - Efficient React rendering
- **Lazy loading** - Components loaded as needed
- **Efficient state updates** - Minimal re-renders

---

This architecture ensures a fast, responsive, and secure local AI experience!
