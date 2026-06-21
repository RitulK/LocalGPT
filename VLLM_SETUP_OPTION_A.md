# vLLM Setup for Nemotron 3 Super
# Option A: Run vLLM on Host Machine (macOS)

## Prerequisites
- 8 GPUs or equivalent GPU memory (the command uses tensor-parallel-size=8)
- Python 3.10+ with conda
- vLLM 0.9.2 or compatible

## Step 1: Create vLLM Environment
```bash
conda create -n vllm python=3.12 -y
conda activate vllm
pip install vllm==0.9.2
```

## Step 2: Clone Nemotron Repository (for tool call support)
```bash
git clone https://huggingface.co/nvidia/Llama-3_3-Nemotron-Super-49B-v1_5
cd Llama-3_3-Nemotron-Super-49B-v1_5
```

## Step 3: Start vLLM Server (from the repo directory)
```bash
conda activate vllm
python3 -m vllm.entrypoints.openai.api_server \
  --model Llama-3_3-Nemotron-Super-49B-v1_5 \
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

## Step 4: Verify vLLM is Running
```bash
curl http://localhost:5000/v1/models
```

Expected output:
```json
{"object":"list","data":[{"id":"Llama-3_3-Nemotron-Super-49B-v1_5","object":"model","created":...,"owned_by":"vllm"}]}
```

## Step 5: Update docker-compose.yml
The backend container will automatically connect to vLLM at `http://host.docker.internal:5000/v1`

No changes needed! The backend already looks for vLLM there by default.

## Step 6: Start LocalGPT (from LocalGPT repo)
```bash
./docker-start.sh
```

## Testing
- Visit `http://localhost:5173`
- Model dropdown should show all Ollama models + "Llama-3_3-Nemotron-Super-49B-v1_5"
- Send a complex reasoning/coding prompt
- ModelRouter should select Nemotron for complex tasks
