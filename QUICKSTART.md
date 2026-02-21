# Quick Start Guide - LocalGPT

## Prerequisites Check

Before starting, ensure you have:

- [ ] **Ollama installed** - Download from [ollama.com](https://ollama.com)
- [ ] **At least one model** - Run `ollama pull llama3.2`
- [ ] **Python 3.8+** - Check with `python3 --version`
- [ ] **Node.js 18+** - Check with `node --version`

## Installation (5 minutes)

### Option 1: Automated Setup (Recommended)

```bash
# Navigate to project directory
cd LocalGPT

# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

The script will:
- ✅ Check all prerequisites
- ✅ Install dependencies
- ✅ Offer to install recommended models
- ✅ Optionally start the application

### Option 2: Manual Setup

#### Step 1: Install Models
```bash
ollama pull llama3.2
ollama pull qwen2.5-coder
```

#### Step 2: Setup Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Step 3: Setup Frontend
```bash
cd frontend
npm install
```

## Running the Application

### Option 1: Using Start Script (Recommended)

```bash
# Make start script executable
chmod +x start.sh

# Start both services
./start.sh
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Access the App

Open your browser and navigate to:
```
http://localhost:5173
```

## First Steps

1. **Verify Connection**
   - Check the status indicator in the top right
   - Should show "Ollama Connected" with a green dot

2. **Select a Model**
   - Choose from the dropdown in the sidebar
   - Or select "🤖 Auto (Router Mode)"

3. **Start Chatting**
   - Type a message and press Enter
   - Watch the response stream in real-time

4. **Try Router Mode**
   - Select "Auto (Router Mode)"
   - Try different types of prompts:
     - "What is Python?" (general)
     - "Write a function to sort an array" (coding)
     - "Analyze the benefits of renewable energy" (reasoning)

5. **Customize Settings**
   - Click the "Settings" tab
   - Set your preferred models
   - Save your configuration

## Common Commands

```bash
# Check Ollama models
ollama list

# Pull a new model
ollama pull <model-name>

# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

## Troubleshooting

### "Ollama Offline" message
```bash
# Start Ollama
ollama serve
```

### "No models found"
```bash
# Install at least one model
ollama pull llama3.2
```

### Backend not starting
```bash
# Check if port 8000 is already in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use a different port if needed (edit backend/main.py)
```

### Frontend not starting
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## What's Next?

- 📚 Read the full [README.md](README.md)
- ⚙️ Check [CONFIGURATION.md](CONFIGURATION.md) for advanced options
- 🎨 Customize the UI and routing logic
- 🚀 Add more models and experiment

## Getting Help

- Check the main README for detailed documentation
- Review the CONFIGURATION guide for customization options
- Visit [Ollama GitHub](https://github.com/ollama/ollama) for model-specific help

---

**You're all set! Happy chatting with your local AI! 🎉**
