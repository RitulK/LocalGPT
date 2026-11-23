# LocalGPT / BuddyAI

A private, local-first AI workspace for chat, documents, memory, model
management, and Obsidian vault integration.

LocalGPT combines FastAPI, React, Ollama, and optional OpenAI-compatible model
providers in one self-hosted interface. Conversations and uploaded knowledge
stay on your machine unless you explicitly enable an external integration.

## Features

- Streaming chat with Ollama and OpenAI-compatible providers
- Automatic or manually selected model routing
- Multiple persistent conversations
- Markdown rendering and code highlighting
- Knowledge-base upload, indexing, search, and RAG responses
- Graph-style personal memory with manual chat and thread capture
- Live web tools through optional TinyFish configuration
- Local model discovery and installation
- Obsidian vault search, note reading, AI-generated drafts, and confirmed writes
- Separate Obsidian permissions for read, create/edit, and delete
- Server-side Obsidian API-key storage and ETag-based write protection

## Obsidian integration

Select an Obsidian tool from the chat composer, enter a normal request, and
review the generated result before it is written to your vault.

Supported chat tools include:

- Add a new note
- Search the vault
- Read or open a note
- Append to a note
- Edit a heading or section
- Replace a note
- Delete a note

Search and note reading use the Obsidian Local REST API directly. Model-assisted
operations generate an editable draft that BuddyAI validates and executes only
after confirmation.

See [Obsidian integration](docs/integrations/obsidian.md) for setup and
security details.

## Requirements

- macOS, Linux, or Windows with Bash support
- Python 3.12
- Node.js and npm
- Ollama
- Git

For Obsidian support:

- Obsidian
- The **Local REST API with MCP** community plugin
- A local plugin API key

## Quick start

Clone the repository:

```bash
git clone https://github.com/RitulK/LocalGPT.git
cd LocalGPT
```

Run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

Start Ollama if it is not already running:

```bash
ollama serve
```

Pull at least one model:

```bash
ollama pull llama3.2
```

Start BuddyAI:

```bash
./start.sh
```

Open:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`

Press `Ctrl+C` to stop the services started by `start.sh`.

## Manual setup

Backend:

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Configuration

The main application settings are available in the BuddyAI Settings panel.

Optional backend environment variables can be placed in `backend/.env`, for
example:

```dotenv
TINYFISH_API_KEY=your_key
TINYFISH_BASE_URL=https://agent.tinyfish.ai/v1/automation
OLLAMA_CLOUD_MODELS_ENABLED=true
```

Do not commit API keys or credentials.

For Docker deployment, see:

- [Docker setup](docs/deployment/docker.md)
- [Configuration guide](docs/getting-started/configuration.md)
- [Troubleshooting](docs/reference/troubleshooting.md)

## Obsidian setup

1. Install and enable **Local REST API with MCP** in Obsidian.
2. Open the plugin settings and copy its API key.
3. Open BuddyAI **Settings → Obsidian**.
4. Set the API address to `https://127.0.0.1:27124`.
5. Enter the API key.
6. Configure certificate verification and the allowed write folder.
7. Test and save the connection.

For a secure HTTPS setup, download the plugin certificate authority from:

```text
https://127.0.0.1:27124/obsidian-local-rest-api.crt
```

Keep delete permission disabled until deletion is explicitly needed.

## Development

Backend:

```bash
backend/venv/bin/python -m compileall -q backend
backend/venv/bin/python -m unittest discover -s backend -p 'test_*.py'
```

Frontend:

```bash
cd frontend
npm run build
npm run dev
```

Repository workflow and architecture notes:

- [Repository guide](repo.md)
- [Project status](project.md)
- [Documentation index](docs/README.md)
- [Development backlog](BACKLOG.md)
- [Changelog](changelog.md)

## Forking and contributing

1. Fork the repository on GitHub.
2. Create a feature branch from the current default branch.
3. Keep changes focused and add tests for new behavior.
4. Run the backend tests and frontend build before opening a pull request.
5. Update the relevant documentation and changelog for user-facing changes.
6. Open a pull request describing the problem, solution, and verification.

Before changing implementation, read [repo.md](repo.md) and
[BACKLOG.md](BACKLOG.md).

## Project structure

```text
backend/
  app/api/            FastAPI route handlers
  app/services/       Application business logic
  app/domain/         Schemas and domain events
  app/infrastructure/ Providers, repositories, and integrations

frontend/
  src/components/     React chat, settings, and feature components
  src/App.jsx         Application state and navigation

docs/                 Integration and deployment documentation
tests/                Playwright end-to-end tests
```

## Documentation

- [Getting started](docs/getting-started/quickstart.md)
- [Configuration](docs/getting-started/configuration.md)
- [Obsidian integration](docs/integrations/obsidian.md)
- [Architecture overview](docs/overview/architecture.md)
- [Troubleshooting](docs/reference/troubleshooting.md)
