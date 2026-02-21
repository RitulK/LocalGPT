# 🤖 LocalGPT Control Center

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)

**A modern, full-stack web application for interacting with local LLMs via Ollama**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [Tech Stack](#-tech-stack)

</div>

---

## 📸 Preview

<div align="center">

### Modern, Beautiful Interface

![LocalGPT Interface](https://via.placeholder.com/800x450/0a0e17/667eea?text=LocalGPT+Control+Center)

*Beautiful gradient design with glass morphism effects and smooth animations*

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎯 Smart Features
- **🤖 Intelligent Model Router** - Automatically selects the best model based on your prompt
- **💬 Real-time Streaming** - Watch responses generate in real-time with SSE
- **📝 Conversation Management** - Save, switch, and manage multiple conversations
- **🎨 Modern UI/UX** - Beautiful gradient design with smooth animations
- **⚡ Fast & Local** - All processing happens on your machine

</td>
<td width="50%">

### 🛠️ Technical Features
- **🔄 Hot Module Replacement** - Instant updates during development
- **📊 Model Management** - View and manage your Ollama models
- **⚙️ Customizable Settings** - Configure defaults and routing behavior
- **🌙 Dark Mode** - Eye-friendly interface (default)
- **📱 Responsive Design** - Works on desktop and tablets

</td>
</tr>
</table>

---

## 🏗️ Architecture

### System Overview

```mermaid
graph TB
    subgraph "Frontend (React + Vite)"
        A[User Interface] --> B[Chat Window]
        A --> C[Sidebar]
        A --> D[Settings Panel]
        B --> E[Message Bubbles]
        C --> F[Conversation List]
    end
    
    subgraph "Backend (FastAPI)"
        G[API Endpoints] --> H[Chat Handler]
        G --> I[Model Manager]
        H --> J[Smart Router]
        H --> K[Ollama Client]
    end
    
    subgraph "Ollama Server"
        L[LLM Models]
        M[qwen:4b]
        N[llama3.2]
        O[qwen2.5-coder]
        L --> M
        L --> N
        L --> O
    end
    
    A -->|HTTP/SSE| G
    K -->|API Calls| L
    J -->|Route Selection| K
    
    style A fill:#667eea,stroke:#764ba2,stroke-width:2px,color:#fff
    style G fill:#4f46e5,stroke:#6366f1,stroke-width:2px,color:#fff
    style L fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
```

### Data Flow

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Frontend
    participant Backend
    participant Router
    participant Ollama
    
    User->>Frontend: Types message
    Frontend->>Backend: POST /chat (SSE stream)
    Backend->>Router: Analyze prompt
    Router->>Router: Detect keywords/code
    Router-->>Backend: Select best model
    Backend->>Ollama: Stream chat request
    loop Streaming Response
        Ollama-->>Backend: Token chunks
        Backend-->>Frontend: SSE events
        Frontend-->>User: Display tokens
    end
    Ollama-->>Backend: Stream complete
    Backend-->>Frontend: Done event
    Frontend->>Frontend: Save conversation
```

### Smart Router Logic

```mermaid
flowchart LR
    A[User Prompt] --> B{Contains Code?}
    B -->|Yes| C[Coding Model]
    B -->|No| D{Reasoning Keywords?}
    D -->|Yes| E[Reasoning Model]
    D -->|No| F{Length > 500?}
    F -->|Yes| G[Reasoning Model]
    F -->|No| H[General Model]
    
    C --> I[qwen2.5-coder]
    E --> J[llama3.2]
    H --> K[qwen:4b]
    
    style A fill:#667eea,stroke:#764ba2,stroke-width:2px,color:#fff
    style C fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    style E fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff
    style H fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#fff
```

---

## 📊 Component Architecture

```mermaid
graph TD
    subgraph "React Components"
        A[App.jsx - Main Container]
        B[Sidebar.jsx]
        C[ChatWindow.jsx]
        D[MessageBubble.jsx]
        E[SettingsPanel.jsx]
        F[ModelManagement.jsx]
        
        A --> B
        A --> C
        A --> E
        A --> F
        C --> D
    end
    
    subgraph "State Management"
        G[Conversations State]
        H[Settings State]
        I[Models State]
        J[Ollama Status]
    end
    
    subgraph "Backend Modules"
        K[main.py - FastAPI App]
        L[router.py - Smart Router]
        M[ollama_client.py - API Client]
    end
    
    A --> G
    A --> H
    A --> I
    A --> J
    
    C -.HTTP.-> K
    K --> L
    K --> M
    
    style A fill:#667eea,stroke:#764ba2,stroke-width:3px,color:#fff
    style K fill:#4f46e5,stroke:#6366f1,stroke-width:3px,color:#fff
```

---

## 🛠️ Tech Stack

<div align="center">

### Frontend Stack

| Technology | Purpose | Version |
|-----------|---------|---------|
| ⚛️ **React** | UI Framework | 18.2 |
| ⚡ **Vite** | Build Tool | 5.0 |
| 🎨 **Tailwind CSS** | Styling | 3.4 |
| 📝 **React Markdown** | Message Rendering | 9.0 |
| 🎯 **Lucide React** | Icons | 0.309 |
| 🎨 **Syntax Highlighter** | Code Display | 15.5 |

### Backend Stack

| Technology | Purpose | Version |
|-----------|---------|---------|
| 🚀 **FastAPI** | Web Framework | 0.115 |
| 🔷 **Pydantic** | Data Validation | 2.9 |
| 🌐 **HTTPX** | HTTP Client | 0.27 |
| ⚡ **Uvicorn** | ASGI Server | 0.32 |

### AI/ML Stack

| Technology | Purpose |
|-----------|---------|
| 🤖 **Ollama** | LLM Runtime |
| 🧠 **qwen:4b** | General Purpose Model |
| 💻 **llama3.2** | Reasoning Model |
| 👨‍💻 **qwen2.5-coder** | Code Generation Model |

</div>

---

## 🎨 UI/UX Features

### Design System

```mermaid
mindmap
  root((LocalGPT Design))
    Colors
      Indigo Primary
      Purple Accent
      Slate Background
      Emerald Success
    Typography
      Inter Font
      Multiple Weights
      Responsive Sizes
    Effects
      Glass Morphism
      Gradient Overlays
      Smooth Animations
      Shadow Depths
    Components
      Rounded Corners
      Backdrop Blur
      Border Gradients
      Hover States
```

### Key UI Elements

- **🎨 Gradient Backgrounds**: Beautiful purple/indigo color schemes
- **✨ Glass Morphism**: Frosted glass effects with backdrop blur
- **🌊 Smooth Animations**: Fade-in, slide-in, and scale transitions
- **💫 Smart Scrolling**: Auto-scroll with smooth/instant modes
- **🎯 Status Indicators**: Animated connection status badges
- **📱 Responsive Layout**: Adapts to different screen sizes

---

## � Installation

### Prerequisites

- **Python 3.12+** (not 3.13/3.14 - compatibility issues)
- **Node.js 18+** and npm
- **Ollama** installed and running

### Step 1: Install Ollama

```bash
# macOS
brew install ollama

# Start Ollama service
ollama serve

# Pull models (in a new terminal)
ollama pull qwen:4b
ollama pull llama3.2
ollama pull qwen2.5-coder
```

### Step 2: Setup Backend

```bash
# Navigate to project
cd LocalGPT

# Create virtual environment
python3.12 -m venv backend/venv

# Activate virtual environment
source backend/venv/bin/activate  # macOS/Linux
# or
backend\venv\Scripts\activate     # Windows

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Step 3: Setup Frontend

```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
npm install
```

---

## 🎮 Usage

### Quick Start

#### Option 1: Automated Scripts (Recommended)

```bash
# Make scripts executable
chmod +x *.sh

# Setup everything
./setup.sh

# Start both servers
./start.sh
```

#### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the Application

1. **Frontend**: Open [http://localhost:5173](http://localhost:5173) or [http://localhost:5174](http://localhost:5174)
2. **Backend API**: [http://localhost:8000](http://localhost:8000)
3. **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🎯 API Endpoints

```mermaid
graph LR
    A[API Routes] --> B[GET /]
    A --> C[POST /chat]
    A --> D[GET /models]
    A --> E[GET /settings]
    A --> F[POST /settings]
    
    B --> B1[Health check]
    C --> C1[Stream chat response]
    D --> D1[List available models]
    E --> E1[Get current settings]
    F --> F1[Update settings]
    
    style A fill:#667eea,stroke:#764ba2,stroke-width:2px,color:#fff
    style C fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
```

### Endpoint Details

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/` | Health check | JSON status |
| `POST` | `/chat` | Stream chat responses | SSE stream |
| `GET` | `/models` | List Ollama models | JSON array |
| `GET` | `/settings` | Get user settings | JSON object |
| `POST` | `/settings` | Update settings | JSON object |
| `GET` | `/docs` | API documentation | Swagger UI |

---

## 📁 Project Structure

```
LocalGPT/
├── 📂 backend/
│   ├── 📂 venv/                # Python virtual environment
│   ├── 📄 main.py              # FastAPI application (279 lines)
│   ├── 📄 router.py            # Smart model router (160 lines)
│   ├── 📄 ollama_client.py     # Ollama API client (142 lines)
│   └── 📄 requirements.txt     # Python dependencies
│
├── 📂 frontend/
│   ├── 📂 src/
│   │   ├── 📂 components/
│   │   │   ├── App.jsx         # Main application
│   │   │   ├── ChatWindow.jsx  # Chat interface
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── SettingsPanel.jsx
│   │   │   └── ModelManagement.jsx
│   │   ├── 📄 main.jsx         # React entry point
│   │   └── 📄 index.css        # Global styles
│   ├── 📄 package.json
│   ├── 📄 vite.config.js
│   └── 📄 tailwind.config.js
│
├── 📂 docs/                    # Documentation
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   └── TROUBLESHOOTING.md
│
├── 📄 setup.sh                 # Automated setup script
├── 📄 start.sh                 # Start servers script
└── 📄 README.md                # You are here!
```

---

## 🔍 Smart Router Patterns

The intelligent router analyzes your prompts and selects the optimal model:

| Pattern | Model Selected | Example Prompts |
|---------|----------------|-----------------|
| 🔧 Code blocks with \`\`\` | **Coding Model** | "Write a Python function..." |
| 💭 Reasoning keywords | **Reasoning Model** | "Explain why...", "Analyze..." |
| 📏 Long prompts (>500 chars) | **Reasoning Model** | Complex multi-part questions |
| 💬 General queries | **General Model** | "What is...", "How to..." |

### Router Keywords

**Coding triggers**: `code`, `function`, `class`, `algorithm`, `debug`, `implement`

**Reasoning triggers**: `why`, `explain`, `analyze`, `compare`, `evaluate`, `reasoning`

---

## � Performance

```mermaid
graph LR
    A[User Input] -->|<50ms| B[Frontend]
    B -->|<100ms| C[Backend]
    C -->|<200ms| D[Ollama]
    D -->|Streaming| E[First Token]
    E -->|1-10 tokens/s| F[Full Response]
    
    style E fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    style F fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
```

- **First token latency**: ~200-400ms
- **Streaming speed**: 1-10 tokens/second (model dependent)
- **UI responsiveness**: 60 FPS animations
- **Memory usage**: ~2-4GB (model dependent)

---

## 🐛 Troubleshooting

<details>
<summary><b>⚠️ Port already in use</b></summary>

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```
</details>

<details>
<summary><b>⚠️ Ollama not running</b></summary>

```bash
# Start Ollama
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```
</details>

<details>
<summary><b>⚠️ No models found</b></summary>

```bash
# Pull recommended models
ollama pull qwen:4b
ollama pull llama3.2
ollama pull qwen2.5-coder

# Verify models
ollama list
```
</details>

<details>
<summary><b>⚠️ CORS errors</b></summary>

Make sure backend `main.py` includes your frontend port in allowed origins:

```python
allow_origins=["http://localhost:5173", "http://localhost:5174"]
```
</details>

<details>
<summary><b>⚠️ Python version issues</b></summary>

Use Python 3.12 (not 3.13 or 3.14):

```bash
# Install Python 3.12
brew install python@3.12

# Create venv with specific version
python3.12 -m venv backend/venv
```
</details>

---

## ⚙️ Configuration

### Backend Settings

Located in `backend/main.py`:

```python
# Default models for router
default_general_model = "qwen:4b"
default_coding_model = "qwen2.5-coder"
default_reasoning_model = "llama3.2"

# Server configuration
host = "0.0.0.0"
port = 8000
```

### Frontend Settings

Located in `frontend/src/App.jsx`:

```javascript
// Initial settings
settings: {
  default_general_model: "qwen:4b",
  default_coding_model: "qwen2.5-coder",
  default_reasoning_model: "llama3.2",
  enable_router: true
}
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. 💾 Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. 📤 Push to the branch (`git push origin feature/AmazingFeature`)
5. 🎉 Open a Pull Request

---

## 🔮 Future Enhancements

- [ ] Multi-model comparison (side-by-side responses)
- [ ] Persistent conversation storage (database)
- [ ] Export conversations to markdown/PDF
- [ ] Voice input/output
- [ ] Model performance analytics
- [ ] Custom system prompts
- [ ] API key for external access
- [ ] Docker containerization
- [ ] RAG (Retrieval Augmented Generation) support

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Ollama Team** - For the amazing local LLM runtime
- **FastAPI** - For the brilliant Python web framework
- **React Team** - For the powerful UI library
- **Tailwind CSS** - For the utility-first CSS framework
- **Lucide Icons** - For beautiful open-source icons

---

## 📞 Support

Having issues? Check out:

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/yourusername/LocalGPT/issues)
- 💬 [Discussions](https://github.com/yourusername/LocalGPT/discussions)

---

<div align="center">

### 🌟 Star this repo if you find it helpful!

Made with ❤️ by the LocalGPT Team

![Footer](https://via.placeholder.com/800x100/0a0e17/667eea?text=LocalGPT+Control+Center+-+Your+AI,+Your+Machine,+Your+Privacy)

</div>
