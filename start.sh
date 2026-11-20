#!/bin/bash

# Start both backend and frontend services

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting LocalGPT...${NC}"
echo ""

BACKEND_PID=""
FRONTEND_PID=""
OLLAMA_PID=""

tinyfish_configured=false
if [ -n "${TINYFISH_API_KEY:-}" ]; then
    tinyfish_configured=true
elif [ -f "backend/.env" ] && grep -q '^TINYFISH_API_KEY=[^[:space:]]' "backend/.env"; then
    tinyfish_configured=true
fi

if [ "$tinyfish_configured" = false ]; then
    echo -e "${BLUE}Note: TinyFish is not configured for LocalGPT.${NC}"
    echo "Add TINYFISH_API_KEY to backend/.env to enable live web tools."
    echo ""
fi

# Check if in correct directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "Error: Please run this script from the LocalGPT root directory"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    [ -n "$OLLAMA_PID" ] && kill "$OLLAMA_PID" 2>/dev/null || true
    rm -f tmp-localgpt-backend.log
    exit 0
}

trap cleanup INT TERM

# Start Ollama if the app or server is not already reachable
if ! curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
    if command -v ollama >/dev/null 2>&1; then
        echo -e "${GREEN}Starting Ollama...${NC}"
        ollama serve >/tmp/localgpt-ollama.log 2>&1 &
        OLLAMA_PID=$!
        for _ in $(seq 1 30); do
            if curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
                break
            fi
            sleep 1
        done
    else
        echo "Error: Ollama is not installed. Install it from https://ollama.com and retry."
        exit 1
    fi
fi

if ! curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "Error: Ollama did not start on http://localhost:11434"
    exit 1
fi

# Start backend with the project virtual environment explicitly
if [ ! -x "backend/venv/bin/python" ]; then
    echo "Error: backend/venv is missing. Run ./setup.sh first."
    exit 1
fi

echo -e "${GREEN}Starting backend...${NC}"
cd backend
venv/bin/python -c "import slowapi, pydantic_settings, structlog" || {
    echo "Error: backend dependencies are incomplete. Run ./setup.sh first."
    cd ..
    exit 1
}
venv/bin/python main.py >../tmp-localgpt-backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
for _ in $(seq 1 30); do
    if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
        break
    fi
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "Error: backend exited during startup."
        cat tmp-localgpt-backend.log
        exit 1
    fi
    sleep 1
done

if ! curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
    echo "Error: backend did not start on http://localhost:8000"
    cat tmp-localgpt-backend.log
    exit 1
fi

# Start frontend
echo -e "${GREEN}Starting frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}✓ Services started${NC}"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait
