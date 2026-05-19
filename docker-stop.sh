#!/bin/bash

# Docker stop script for LocalGPT

echo "🛑 Stopping LocalGPT containers..."

docker-compose down

echo ""
echo "✅ All services stopped!"
echo ""
echo "💡 To remove volumes (models will need to be re-downloaded):"
echo "   docker-compose down -v"
echo ""
