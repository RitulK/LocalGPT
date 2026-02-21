#!/bin/bash

# Test script to verify LocalGPT installation

echo "🧪 LocalGPT Installation Test"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

# Test function
test_check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAILED++))
    fi
}

# Check Ollama
echo "Checking Ollama..."
command -v ollama &> /dev/null
test_check "Ollama is installed"

curl -s http://localhost:11434/api/tags > /dev/null 2>&1
test_check "Ollama is running"

# Check models
MODEL_COUNT=$(ollama list 2>/dev/null | tail -n +2 | wc -l | tr -d ' ')
if [ "$MODEL_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✓${NC} Found $MODEL_COUNT Ollama model(s)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} No Ollama models found (install with: ollama pull llama3.2)"
    ((FAILED++))
fi

# Check Python
echo ""
echo "Checking Python..."
command -v python3 &> /dev/null
test_check "Python 3 is installed"

# Check Node.js
echo ""
echo "Checking Node.js..."
command -v node &> /dev/null
test_check "Node.js is installed"

command -v npm &> /dev/null
test_check "npm is installed"

# Check backend files
echo ""
echo "Checking backend files..."
[ -f "backend/main.py" ]
test_check "backend/main.py exists"

[ -f "backend/router.py" ]
test_check "backend/router.py exists"

[ -f "backend/ollama_client.py" ]
test_check "backend/ollama_client.py exists"

[ -f "backend/requirements.txt" ]
test_check "backend/requirements.txt exists"

# Check frontend files
echo ""
echo "Checking frontend files..."
[ -f "frontend/package.json" ]
test_check "frontend/package.json exists"

[ -f "frontend/src/App.jsx" ]
test_check "frontend/src/App.jsx exists"

[ -f "frontend/src/components/ChatWindow.jsx" ]
test_check "frontend/src/components/ChatWindow.jsx exists"

# Check backend dependencies
echo ""
echo "Checking backend setup..."
if [ -d "backend/venv" ]; then
    echo -e "${GREEN}✓${NC} Python virtual environment exists"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Python virtual environment not found (run: cd backend && python3 -m venv venv)"
    ((FAILED++))
fi

# Check frontend dependencies
echo ""
echo "Checking frontend setup..."
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✓${NC} Node modules installed"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Node modules not installed (run: cd frontend && npm install)"
    ((FAILED++))
fi

# Summary
echo ""
echo "=============================="
echo "Test Summary:"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! You're ready to run LocalGPT.${NC}"
    echo ""
    echo "To start the application, run:"
    echo "  ./start.sh"
    echo ""
    echo "Or manually:"
    echo "  Terminal 1: cd backend && source venv/bin/activate && python main.py"
    echo "  Terminal 2: cd frontend && npm run dev"
else
    echo -e "${YELLOW}⚠ Some checks failed. Please review the errors above.${NC}"
    echo ""
    echo "To set up the application, run:"
    echo "  ./setup.sh"
fi
