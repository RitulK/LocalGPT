# LocalGPT Documentation

Welcome to the LocalGPT documentation. Everything you need to understand, run, deploy, and extend the project lives in this folder.

> Looking for the top-level overview? See [README.md](../README.md) at the repo root.

---

## 📚 Index

### � Overview — what LocalGPT is and how it works
- [architecture.md](overview/architecture.md) — System architecture, data flow, and component diagram
- [model-router.md](overview/model-router.md) — Hierarchical routing system deep dive
- [project-summary.md](overview/project-summary.md) — High-level summary of features and structure

### 🚀 Getting Started — install and configure
- [quickstart.md](getting-started/quickstart.md) — Prerequisites and fastest path to a running app
- [configuration.md](getting-started/configuration.md) — Recommended model setup and env variables

### � Deployment — run it anywhere
- [docker.md](deployment/docker.md) — Docker setup guide (compose, hosts, networking)
- [build-complete.md](deployment/build-complete.md) — Complete build summary and verification checklist

### 🔌 Integrations — extra model backends and UI features
- [nvidia-nemotron.md](integrations/nvidia-nemotron.md) — NVIDIA Nemotron 3 Ultra cloud API + extended thinking
- [nemotron-vllm.md](integrations/nemotron-vllm.md) — Local Nemotron Super 49B via vLLM
- [vllm-setup-macos.md](integrations/vllm-setup-macos.md) — Option A: run vLLM on macOS host
- [vllm-setup-docker.md](integrations/vllm-setup-docker.md) — Option B: run vLLM in Docker (Linux/cloud)
- [frontend-thinking.md](integrations/frontend-thinking.md) — Frontend SSE wiring for reasoning UI

### 🛠️ Reference — fix things when they break
- [troubleshooting.md](reference/troubleshooting.md) — Python, Docker, model, and connectivity issues

---

## 🗂️ Folder Layout

```
docs/
├── README.md                       ← you are here
├── overview/                       ← what & how
├── getting-started/                ← install & configure
├── deployment/                     ← docker & build
├── integrations/                   ← extra models & UI
└── reference/                      ← troubleshooting
```

---

## � Contributing

When adding new docs, please:
1. Pick the most appropriate sub-folder (or create one if a new category is needed).
2. Use lowercase, hyphen-separated filenames (`my-feature.md`).
3. Link to your new doc from this index.
