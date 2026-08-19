# Docker Compose with vLLM Service
# Option B: Run vLLM in Docker

## ⚠️ Important Notes for macOS Users
- Docker Desktop on macOS has limited GPU support
- For best performance, vLLM should run on a Linux machine or cloud GPU
- Option A (vLLM on host) is recommended for macOS

## If Running on Linux with GPU Support:

### Step 1: Update docker-compose.yml
Replace the docker-compose.yml content with:

```yaml
services:
  # Backend service - FastAPI server
  backend:
    build:
      context: .
      dockerfile: dockerfile
    container_name: localgpt-backend
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://host.docker.internal:11434
      - VLLM_BASE_URL=http://vllm:5000/v1
      - DOCKER_ENV=1
    restart: unless-stopped
    volumes:
      - ./backend:/app
    depends_on:
      - vllm
    networks:
      - localgpt-network

  # vLLM service for Nemotron
  vllm:
    image: vllm/vllm-openai:latest
    container_name: localgpt-vllm
    ports:
      - "5000:8000"
    environment:
      - HUGGINGFACE_HUB_CACHE=/workspace/model_cache
    volumes:
      - ./model_cache:/workspace/model_cache
      - ./Llama-3_3-Nemotron-Super-49B-v1_5:/workspace/Nemotron
    working_dir: /workspace
    command: >
      python3 -m vllm.entrypoints.openai.api_server
      --model /workspace/Nemotron
      --trust-remote-code
      --seed=1
      --host=0.0.0.0
      --port=8000
      --served-model-name "Llama-3_3-Nemotron-Super-49B-v1_5"
      --tensor-parallel-size=8
      --max-model-len=65536
      --gpu-memory-utilization 0.95
    restart: unless-stopped
    shm_size: '16gb'
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 8
              capabilities: [gpu]
    networks:
      - localgpt-network

  # Frontend service - React + Vite
  frontend:
    build:
      context: .
      dockerfile: frontend.dockerfile
    container_name: localgpt-frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - localgpt-network

networks:
  localgpt-network:
    driver: bridge
```

### Step 2: Prerequisites
```bash
# Install NVIDIA Docker runtime (Linux only)
# https://github.com/NVIDIA/nvidia-docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.0-runtime nvidia-smi
```

### Step 3: Clone Nemotron Repository
```bash
git clone https://huggingface.co/nvidia/Llama-3_3-Nemotron-Super-49B-v1_5
```

### Step 4: Start Services
```bash
docker-compose up -d
```

### Step 5: Monitor vLLM startup (may take 5-10 minutes to load the model)
```bash
docker logs -f localgpt-vllm
```

### Step 6: Verify
```bash
curl http://localhost:5000/v1/models
```

## For macOS Users
**Recommendation:** Use Option A (vLLM on host machine running natively)
