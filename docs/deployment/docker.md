# 🐳 Docker Setup Guide for LocalGPT

This guide explains how to run LocalGPT using Docker.

## 📋 Prerequisites

- **Docker Desktop** installed and running
- **Docker Compose** (included with Docker Desktop)
- **Ollama for macOS** installed and running natively at http://localhost:11434
- At least **8GB RAM** available
- **10GB+ disk space** for models

## 🚀 Quick Start

### 1. Start All Services

```bash
# Make scripts executable (first time only)
chmod +x docker-start.sh docker-stop.sh

# Start everything (builds on first run)
./docker-start.sh
```

The script will:
- ✅ Build all containers
- ✅ Start Backend and Frontend containers
- ✅ Verify native Ollama is reachable on your Mac
- ✅ Display access URLs

### 2. Access the Application

Once started, open your browser:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434

### 3. Stop Services

```bash
./docker-stop.sh
```

## 🔧 Manual Commands

### Build Containers

```bash
docker-compose build
```

### Start Services

```bash
docker-compose up -d
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Volumes

```bash
docker-compose down -v
```

## 📦 Service Architecture

### 1. Native Ollama
- **Host**: macOS app/process
- **Port**: 11434
- **Purpose**: Runs LLM models locally with Apple Metal acceleration

### 2. Backend Service
- **Container**: `localgpt-backend`
- **Port**: 8000
- **Framework**: FastAPI + Python 3.12
- **Purpose**: API server with smart routing; connects to `http://host.docker.internal:11434`

### 3. Frontend Service
- **Container**: `localgpt-frontend`
- **Port**: 5173
- **Framework**: React + Vite
- **Purpose**: Web UI

## 🎯 Download Models

Install models with native Ollama on your Mac:

```bash
ollama pull qwen:4b
ollama pull llama3.2
ollama pull qwen2.5-coder

# List installed models
ollama list
```

## 🔍 Troubleshooting

### Container Won't Start

```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs backend
```

### Port Conflicts

If ports 8000, 5173, or 11434 are in use:

```bash
# Find what's using the port
lsof -i :8000
lsof -i :5173
lsof -i :11434

# Kill the process
kill -9 <PID>
```

Or edit `docker-compose.yml` to use different ports:

```yaml
ports:
  - "8001:8000"  # Change host port
```

### Rebuild Containers

```bash
# Rebuild everything from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Reset Everything

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
./docker-start.sh
```

### Check Ollama Connection

```bash
# From host
curl http://localhost:11434/api/tags

# From backend container
docker exec localgpt-backend curl http://host.docker.internal:11434/api/tags
```

## 🎮 GPU/Metal Support

On macOS, run Ollama natively instead of inside Docker. Native Ollama can use Apple Metal acceleration, while the backend/frontend still run in Docker.

## 📊 Resource Usage

### Check Container Resources

```bash
# Real-time stats
docker stats

# Container resource usage
docker-compose top
```

### Typical Usage
- **Native Ollama**: model-dependent; smaller models use less RAM and respond faster
- **Backend**: 100-200MB RAM
- **Frontend**: 50-100MB RAM

## 🔄 Development Mode

The current setup uses **development mode** with hot reloading:

- **Backend**: Auto-reloads on code changes
- **Frontend**: Vite HMR (Hot Module Replacement)

Both services mount source code as volumes for instant updates.

### Production Mode

For production, modify dockerfiles:

**Frontend** (frontend.dockerfile):
```dockerfile
# Build stage
RUN npm run build

# Serve built files
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
```

**Backend** (dockerfile):
```dockerfile
# Remove volume mount in docker-compose.yml
# Use production-grade server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## 📁 File Structure

```
LocalGPT/
├── docker-compose.yml      # Orchestrates all services
├── dockerfile              # Backend container
├── frontend.dockerfile     # Frontend container
├── .dockerignore          # Excludes files from build
├── docker-start.sh        # Start script
└── docker-stop.sh         # Stop script
```

## 🌐 Networking

All services are on the `localgpt-network` bridge:

- Backend → Native Ollama: `http://host.docker.internal:11434`
- Frontend → Backend: `http://backend:8000` (internal)
- Host → Frontend: `http://localhost:5173`
- Host → Backend: `http://localhost:8000`

## 💡 Tips

1. **Install models natively** - use `ollama pull <model>` on your Mac
2. **Keep native Ollama running** - the backend depends on it
3. **Check logs** if something fails - they're very helpful
4. **Models persist** - stored by native Ollama, outside Docker
5. **Dev changes instant** - both backend and frontend hot reload

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| "Port already in use" | Stop conflicting service or change port |
| "Cannot connect to Ollama" | Start native Ollama and check `curl http://localhost:11434/api/tags` |
| "Models not found" | Run `ollama pull <model>` on your Mac |
| "Frontend won't load" | Check backend is running, check CORS settings |
| "Slow responses" | Use smaller models, keep context short, and verify native Ollama is being used |

## 📝 Environment Variables

Set in `docker-compose.yml`:

```yaml
environment:
  - OLLAMA_HOST=http://host.docker.internal:11434
  - VITE_API_URL=http://localhost:8000
```

---

Happy Docker-ing! 🐳✨
