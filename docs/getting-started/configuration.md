# LocalGPT Example Configuration

## Recommended Model Setup

For optimal experience, install these Ollama models:

### 1. General Purpose
```bash
# Fast, capable general model
ollama pull llama3.2

# Alternative: Larger model for better quality
ollama pull llama3.2:70b
```

### 2. Coding & Development
```bash
# Code-specialized model
ollama pull qwen2.5-coder

# Alternative: CodeLlama
ollama pull codellama
```

### 3. Reasoning & Analysis
```bash
# Same as general for now
# Or use any larger model you prefer
ollama pull llama3.2
```

## Settings Configuration

After starting the app, configure these settings:

1. Navigate to **Settings** tab
2. Set default models:
   - **General Conversations**: `llama3.2:latest`
   - **Coding & Development**: `qwen2.5-coder:latest`
   - **Reasoning & Analysis**: `llama3.2:latest`
3. Enable **Router Mode** (recommended)
4. Click **Save Settings**

## Example Prompts

### Test General Model
```
What is the capital of France?
```

### Test Coding Model (Auto-routes to coding model)
```
Write a Python function to calculate the Fibonacci sequence
```

### Test Reasoning Model (Auto-routes to reasoning model)
```
Analyze the pros and cons of electric vehicles compared to traditional cars. Consider environmental impact, cost, and practicality.
```

### Test with Code Block (Auto-routes to coding model)
```
Please review this code:

```python
def hello():
    print("Hello World")
```

What improvements can be made?
```

## Port Configuration

### Backend (default: 8000)
Edit `backend/main.py`:
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Change port here
```

### Frontend (default: 5173)
Edit `frontend/vite.config.js`:
```javascript
export default defineConfig({
  server: {
    port: 5173,  // Change port here
  }
})
```

## Ollama Configuration

### Set GPU Layers (if you have GPU)
```bash
# For NVIDIA GPU
ollama run llama3.2 --num-gpu 35

# Check GPU usage
nvidia-smi
```

### Memory Optimization
```bash
# Set memory limit (e.g., 8GB)
OLLAMA_MAX_MEMORY=8g ollama serve
```

### Model Storage Location
```bash
# Default locations:
# macOS: ~/.ollama/models
# Linux: /usr/share/ollama/.ollama/models
# Windows: C:\Users\<user>\.ollama\models

# Set custom location
export OLLAMA_MODELS=/path/to/models
```

## Environment Variables

### Backend (.env file in backend/)
```bash
# Ollama API URL
OLLAMA_BASE_URL=http://localhost:11434

# Server configuration
HOST=0.0.0.0
PORT=8000

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (.env file in frontend/)
```bash
# API endpoint
VITE_API_URL=http://localhost:8000
```

## Custom Router Rules

Edit `backend/router.py` to add custom routing logic:

```python
# Example: Route medical queries to a medical model
if "medical" in prompt_lower or "health" in prompt_lower:
    return "meditron:latest"  # If you have this model installed

# Example: Route math queries to a specialized model
if any(word in prompt_lower for word in ["calculate", "math", "equation"]):
    return "math-model:latest"
```

## Performance Tuning

### Small Models (Fast, Lower Quality)
```bash
ollama pull llama3.2:1b   # ~1GB, very fast
```

### Medium Models (Balanced)
```bash
ollama pull llama3.2:3b   # ~2GB, good balance
ollama pull llama3.2:8b   # ~4GB, higher quality
```

### Large Models (Slow, Higher Quality)
```bash
ollama pull llama3.2:70b  # ~40GB, best quality
```

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

### Frontend won't start
```bash
# Check if port 5173 is in use
lsof -i :5173

# Or use a different port
npm run dev -- --port 3000
```

### Ollama connection issues
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Restart Ollama
pkill ollama
ollama serve
```

### Model not found error
```bash
# Verify model is installed
ollama list

# Install missing model
ollama pull <model-name>
```

## Advanced Configuration

### Add Custom Model to Router

1. Install your model via Ollama
2. Edit `backend/router.py`
3. Add to default models or routing logic
4. Update Settings UI to include new model option

### Customize UI Theme

Edit `frontend/tailwind.config.js`:
```javascript
theme: {
  extend: {
    colors: {
      primary: '#3b82f6',  // Change primary color
      // Add more custom colors
    }
  }
}
```

### Add System Prompts

Edit the chat request in `frontend/src/components/ChatWindow.jsx`:
```javascript
const messages = [
  {
    role: "system",
    content: "You are a helpful AI assistant..."
  },
  ...request.conversation_history,
  {
    role: "user",
    content: request.prompt
  }
];
```
