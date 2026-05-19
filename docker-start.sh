#!/bin/bash

# Docker startup script for LocalGPT

echo "🚀 Starting LocalGPT with Docker..."
echo ""

# Build and start all services
echo "📦 Building containers..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Wait for Ollama to be ready
echo "🤖 Checking Ollama service..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "   Waiting for Ollama to start..."
    sleep 2
done
echo "✅ Ollama is running!"

# Pull recommended models (if not already present)
echo ""
echo "📥 Checking for required models..."
echo "   This may take several minutes on first run..."

docker exec localgpt-ollama ollama pull qwen:4b
docker exec localgpt-ollama ollama pull llama3.2
docker exec localgpt-ollama ollama pull qwen2.5-coder

echo ""
echo "✨ LocalGPT is ready!"
echo ""
echo "🌐 Access points:"
echo "   Frontend:  http://localhost:5173"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Ollama:    http://localhost:11434"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
