# Nvidia Nemotron 3 Ultra Integration Guide

## Overview
This guide explains how to integrate **Nvidia's Nemotron 3 Ultra** model (550B parameters) with extended thinking/reasoning capabilities into LocalGPT.

## What is Nemotron 3 Ultra?
- **550B parameters** - Nvidia's most powerful open model
- **Reasoning capabilities** - Built-in extended thinking for complex problems
- **Cloud-hosted** - Runs on Nvidia's infrastructure, no local GPU needed
- **OpenAI-compatible API** - Easy integration via standard OpenAI client

## Getting Started

### Step 1: Get Your Nvidia API Key

1. Visit **https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b**
2. Sign in or create a Nvidia account (free)
3. Click **"Get API Key"**
4. Copy your API key

### Step 2: Set Environment Variable

#### Option A: Direct (for testing)
```bash
export NVIDIA_API_KEY="your-api-key-here"
```

#### Option B: Docker Compose (recommended)
Edit `docker-compose.yml` and add to backend service:
```yaml
services:
  backend:
    environment:
      - OLLAMA_HOST=http://host.docker.internal:11434
      - NVIDIA_API_KEY=your-api-key-here
```

#### Option C: .env file
Create `.env` in your project root and add:
```
NVIDIA_API_KEY=your-api-key-here
```

### Step 3: Start LocalGPT

```bash
./docker-start.sh
```

The backend will automatically detect your API key and enable Nvidia models.

### Step 4: Verify Integration

```bash
# Check if Nemotron appears in model list
curl http://localhost:8000/models

# Should include:
# "name": "nvidia/nemotron-3-ultra-550b-a55b",
# "provider": "nvidia"
```

## Using the Model

### Via Frontend

1. Open **http://localhost:5173**
2. Model dropdown now includes **"nvidia/nemotron-3-ultra-550b-a55b"**
3. Select it for your chat

### Enable Thinking/Reasoning

#### In Frontend (if UI updated)
- Look for **"Enable Extended Thinking"** toggle
- When enabled, the model will spend time reasoning before answering

#### Via API
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze this complex algorithm and explain its time complexity",
    "model": "nvidia/nemotron-3-ultra-550b-a55b",
    "enable_thinking": true,
    "reasoning_budget": 8192
  }'
```

### Request Parameters

```json
{
  "prompt": "Your question here",
  "model": "nvidia/nemotron-3-ultra-550b-a55b",
  "enable_thinking": true,              // Enable reasoning (optional)
  "reasoning_budget": 8192,             // Max tokens for thinking (optional)
  "use_router": false,                  // Don't use router, use this model directly
  "conversation_id": 1,                 // Conversation ID (optional)
  "use_rag": false                      // Use knowledge base (optional)
}
```

## How Thinking/Reasoning Works

### When Enabled
1. Model performs internal reasoning before generating response
2. Thinking process is hidden from user (or can be displayed)
3. Final answer is more thoughtful and accurate

### Best Use Cases for Thinking
- Complex mathematical problems
- Multi-step reasoning tasks
- Algorithm analysis
- Code review and optimization
- Scientific explanations
- Philosophical discussions

### Reasoning Budget
- **8192 tokens** (default) - Good for most tasks
- **16384 tokens** - For very complex problems
- **Max 32000 tokens** - Model limit for thinking

## Model Selection by Router

The intelligent router will automatically select Nemotron 3 Ultra for:
- Complex reasoning questions
- Deep analysis requests
- Advanced coding problems
- Research questions
- Abstract problem solving

Example prompts that trigger Nemotron selection:
- "Analyze and explain this algorithm's complexity"
- "Why does quantum entanglement work this way?"
- "Design a scalable database architecture for..."
- "Compare different approaches to solving..."

## Response Format

When thinking is enabled, responses include:

```json
{
  "type": "metadata",
  "model": "nvidia/nemotron-3-ultra-550b-a55b",
  "thinking_enabled": true
}

{
  "type": "reasoning",
  "content": "Let me think about this step by step..."
}

{
  "type": "content",
  "content": "Based on my analysis..."
}
```

## Troubleshooting

### "NVIDIA_API_KEY environment variable not set"
```bash
# Check if key is set
echo $NVIDIA_API_KEY

# If empty, set it:
export NVIDIA_API_KEY="your-key"

# Then restart Docker
./docker-stop.sh
./docker-start.sh
```

### "Nvidia API authentication failed"
- Verify API key is correct from https://build.nvidia.com
- Ensure there are no extra spaces in the key
- Check that your Nvidia account is active

### "Failed to connect to Nvidia API"
- Check internet connectivity
- Verify Nvidia API is accessible from your network
- Check firewall/proxy settings if in corporate environment

### Model Not Appearing in Dropdown
```bash
# Check backend models endpoint
curl http://localhost:8000/models | jq

# If Nemotron not listed, check backend logs
docker logs localgpt-backend | grep -i nvidia
```

### Slow Responses
- Nemotron 3 Ultra is a massive model - responses take 2-10 seconds
- This is normal - you're using the most powerful model
- For faster responses, use Qwen models (faster, still high quality)

## Comparison: Nemotron 3 Ultra vs Local Models

| Aspect | Qwen 4B | Qwen 7B Coder | Nemotron Ultra |
|--------|---------|--------------|---|
| Speed | ⚡⚡⚡ Very Fast | ⚡⚡ Fast | ⚡ Slower |
| Reasoning | ⭐⭐⭐ Good | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Best |
| Coding | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Expert | ⭐⭐⭐⭐⭐ Expert |
| Context | ⭐⭐⭐ Good | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Best |
| Cost | Free (local) | Free (local) | Cloud credits |
| Internet Required | No | No | Yes |
| Local GPU Required | Yes | Yes | No |

## API Key Security

### Important Security Notes
- ⚠️ Never commit API key to git
- ⚠️ Don't share your API key publicly
- ⚠️ Store in environment variables, not in code
- ⚠️ Use .env file locally, secrets management in production

### For Production
```bash
# Use Docker secrets
docker secret create nvidia_api_key /path/to/secret

# Or use environment variable from CI/CD (GitHub Actions, etc.)
```

## Advanced Configuration

### Custom Settings
Update default thinking behavior in `docker-compose.yml`:
```yaml
environment:
  - NVIDIA_API_KEY=your-key
  - VLLM_API_KEY=dummy  # If also using vLLM
```

### Update Settings via API
```bash
curl -X POST http://localhost:8000/settings \
  -H "Content-Type: application/json" \
  -d '{
    "enable_thinking": true,
    "reasoning_budget": 10000
  }'
```

## API Limits and Costs
- **Rate limits**: Check your Nvidia account at https://build.nvidia.com
- **Credits**: Free tier includes usage credits
- **Costs**: Metered based on tokens consumed
- **Monitoring**: Use Nvidia dashboard to track usage

## Support and Resources
- **Nvidia Documentation**: https://docs.nvidia.com/ai-enterprise/rag/latest/
- **Model Card**: https://huggingface.co/nvidia/Llama-3_3-Nemotron-Super-49B-v1_5
- **API Docs**: https://docs.nvidia.com/api/nemotron-api/
- **Forum**: https://forums.developer.nvidia.com/
