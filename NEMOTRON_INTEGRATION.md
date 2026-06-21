# Nemotron 3 Super Integration Guide

## What Changed

### New Files
1. **backend/vllm_client.py** - Client for vLLM OpenAI-compatible API
2. **VLLM_SETUP_OPTION_A.md** - Run vLLM on macOS host
3. **VLLM_SETUP_OPTION_B.md** - Run vLLM in Docker (for Linux/cloud)

### Updated Files
1. **backend/main.py**
   - Import vllm_client
   - Initialize both OllamaClient and VLLMClient
   - `/models` endpoint now returns Ollama + vLLM models
   - `/chat` endpoint routes to correct client based on model

2. **backend/router.py**
   - Added Nemotron to MODEL_CAPABILITIES
   - Nemotron has highest scores for reasoning (9), coding (9), context (10)
   - Router will auto-select Nemotron for complex reasoning/coding tasks

## Quick Start (Recommended for macOS)

### Step 1: Pull Nemotron Model Repository
```bash
git clone https://huggingface.co/nvidia/Llama-3_3-Nemotron-Super-49B-v1_5
```

### Step 2: Start vLLM Server (in a new terminal)
```bash
cd Llama-3_3-Nemotron-Super-49B-v1_5

# Create/activate vLLM environment
conda create -n vllm python=3.12 -y
conda activate vllm
pip install vllm==0.9.2

# Start server
python3 -m vllm.entrypoints.openai.api_server \
  --model . \
  --trust-remote-code \
  --seed=1 \
  --host="0.0.0.0" \
  --port=5000 \
  --served-model-name "Llama-3_3-Nemotron-Super-49B-v1_5" \
  --tensor-parallel-size=8 \
  --max-model-len=65536 \
  --gpu-memory-utilization 0.95 \
  --enforce-eager
```

### Step 3: Start LocalGPT (in your LocalGPT repo directory)
```bash
./docker-start.sh
```

### Step 4: Use in Frontend
- Open http://localhost:5173
- Model dropdown now shows all Ollama models + Nemotron
- Send complex reasoning prompts → Router selects Nemotron automatically
- Or manually select Nemotron from dropdown

## How It Works

### Model Selection Flow
1. User sends a prompt
2. If `use_router=true`, ModelRouter analyzes the prompt
3. For complex reasoning/coding → Nemotron (vLLM) selected
4. For general chat → Qwen models (Ollama) selected
5. Correct client (OllamaClient or VLLMClient) streams response

### Auto-Discovery
- `/models` endpoint detects available models:
  - Ollama models: `qwen:4b`, `qwen2.5-coder:7b`, etc.
  - vLLM models: `Llama-3_3-Nemotron-Super-49B-v1_5`
- Frontend displays all models in dropdown

## Troubleshooting

### vLLM server not connecting?
```bash
# Verify vLLM is running and accessible
curl http://localhost:5000/v1/models

# Check backend logs
docker logs localgpt-backend
```

### Model not appearing in dropdown?
```bash
# Check which models are available
curl http://localhost:8000/models

# Should show both Ollama and Nemotron models
```

### vLLM failing to load model?
- Check you have 8 GPUs or equivalent VRAM
- Model requires ~49B parameters with high tensor parallelism
- Run `nvidia-smi` to verify GPU availability

### Router not selecting Nemotron?
- Complex prompts with "reasoning", "analyze", "explain", "code" keywords trigger Nemotron
- Try: "Analyze the following algorithm and explain how it works"
- ModelRouter logs to console (watch docker logs)

## Model Capabilities Comparison

| Aspect | Qwen 4B | Qwen 7B Coder | Nemotron 49B |
|--------|---------|--------------|-------------|
| Speed | 9/10 | 7/10 | 5/10 |
| Reasoning | 6/10 | 7/10 | 9/10 |
| Coding | 7/10 | 10/10 | 9/10 |
| Context | 8/10 | 8/10 | 10/10 |
| Writing | 8/10 | 6/10 | 9/10 |

## Configuration

### Custom vLLM URL
Set environment variable in docker-compose.yml:
```yaml
environment:
  - VLLM_BASE_URL=http://custom-host:5000/v1
```

### Custom vLLM API Key
```yaml
environment:
  - VLLM_API_KEY=your-api-key
```

### Disable vLLM
Just remove the vllm_client initialization and it will gracefully fail with a warning when fetching models.
