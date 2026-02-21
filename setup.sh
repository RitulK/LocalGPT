#!/bin/bash

# LocalGPT Setup Script
# This script sets up and runs the LocalGPT application

set -e  # Exit on error

echo "🚀 LocalGPT Setup Script"
echo "========================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if Ollama is installed
echo "Checking prerequisites..."
if ! command -v ollama &> /dev/null; then
    print_error "Ollama is not installed"
    echo "Please install Ollama from: https://ollama.com"
    exit 1
else
    print_status "Ollama is installed"
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_warning "Ollama is not running"
    echo "Starting Ollama service..."
    ollama serve &
    sleep 3
fi

# Check if any models are installed
MODEL_COUNT=$(ollama list | tail -n +2 | wc -l | tr -d ' ')
if [ "$MODEL_COUNT" -eq "0" ]; then
    print_warning "No Ollama models found"
    echo "Would you like to install recommended models? (y/n)"
    read -r INSTALL_MODELS
    
    if [ "$INSTALL_MODELS" = "y" ] || [ "$INSTALL_MODELS" = "Y" ]; then
        echo "Installing llama3.2..."
        ollama pull llama3.2
        echo "Installing qwen2.5-coder..."
        ollama pull qwen2.5-coder
        print_status "Models installed successfully"
    else
        print_warning "Continuing without models. You can install them later with: ollama pull <model-name>"
    fi
else
    print_status "Found $MODEL_COUNT Ollama model(s)"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python $PYTHON_VERSION is installed"
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed"
    exit 1
else
    NODE_VERSION=$(node --version)
    print_status "Node.js $NODE_VERSION is installed"
fi

echo ""
echo "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip

# Install dependencies preferring binary packages (no building from source)
echo "Installing FastAPI and dependencies (this may take a minute)..."
pip install -q --prefer-binary -r requirements.txt || {
    echo ""
    print_warning "Standard installation failed. Trying alternative method..."
    echo "This might happen with newer Python versions (3.13+)."
    echo "Installing with --only-binary for compatible packages..."
    pip install fastapi uvicorn httpx python-multipart --prefer-binary
    pip install "pydantic>=2.0,<3.0" --prefer-binary || {
        print_error "Failed to install dependencies."
        echo ""
        echo "Your Python version: $(python3 --version)"
        echo "Recommended: Python 3.9 - 3.12"
        echo ""
        echo "Options:"
        echo "1. Use Python 3.9-3.12 (recommended)"
        echo "2. Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
        exit 1
    }
}
print_status "Backend dependencies installed"

echo ""
echo "Setting up frontend..."
cd ../frontend

# Install Node dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    print_status "Frontend dependencies installed"
else
    print_status "Frontend dependencies already installed"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""

# Ask if user wants to start now
echo "Would you like to start the application now? (y/n)"
read -r START_NOW

if [ "$START_NOW" = "y" ] || [ "$START_NOW" = "Y" ]; then
    echo ""
    echo "Starting backend..."
    cd ../backend
    source venv/bin/activate
    python main.py &
    BACKEND_PID=$!
    
    echo "Waiting for backend to start..."
    sleep 3
    
    echo "Starting frontend..."
    cd ../frontend
    npm run dev &
    FRONTEND_PID=$!
    
    echo ""
    print_status "Application is running!"
    echo ""
    echo "Backend: http://localhost:8000"
    echo "Frontend: http://localhost:5173"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
    wait
fi
