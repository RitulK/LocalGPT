# Installation Troubleshooting

## Python 3.13+ / 3.14 Issues

If you're using Python 3.13 or 3.14 and getting errors about building wheels or Rust not found:

### Option 1: Use Python 3.12 (Recommended)

```bash
# Install Python 3.12 via pyenv
brew install pyenv
pyenv install 3.12.7
pyenv local 3.12.7

# Then run setup
./setup.sh
```

### Option 2: Install Rust

```bash
# Install Rust (required for building pydantic-core)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Restart terminal, then run
./setup.sh
```

### Option 3: Manual Installation with Alternative Packages

```bash
cd backend
python3 -m venv venv
source venv/bin/activate

# Install one by one to avoid build issues
pip install --upgrade pip
pip install fastapi
pip install uvicorn[standard]
pip install httpx
pip install python-multipart

# Try pydantic with prefer-binary
pip install --prefer-binary "pydantic>=2.0,<3.0"

# If that fails, use older version
pip install pydantic==2.8.2
```

## Common Errors

### Error: "Failed building wheel for pydantic-core"
**Cause**: Python 3.13+ requires Rust to build pydantic-core  
**Solution**: Use Python 3.9-3.12 or install Rust

### Error: "Rust not found"
**Cause**: pydantic-core needs Rust compiler  
**Solution**: 
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### Error: "No module named 'pydantic'"
**Cause**: Installation didn't complete  
**Solution**: Check Python version and reinstall:
```bash
python3 --version  # Should be 3.9-3.12 for best compatibility
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Port 8000 already in use"
**Cause**: Another process using port 8000  
**Solution**:
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or edit backend/main.py to use different port
```

### Error: "Cannot connect to Ollama"
**Cause**: Ollama not running  
**Solution**:
```bash
# Start Ollama
ollama serve

# In another terminal, verify
curl http://localhost:11434/api/tags
```

## Python Version Compatibility

| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.8 | ✅ Supported | Stable |
| 3.9 | ✅ Supported | Recommended |
| 3.10 | ✅ Supported | Recommended |
| 3.11 | ✅ Supported | Recommended |
| 3.12 | ✅ Supported | **Best choice** |
| 3.13 | ⚠️ Works | Requires Rust or --prefer-binary |
| 3.14 | ⚠️ Beta | May require Rust, not recommended |

## Quick Fix Commands

```bash
# Check your Python version
python3 --version

# If 3.13+, switch to 3.12
brew install python@3.12
python3.12 -m venv venv
source venv/bin/activate

# Verify you're using the right Python
which python
python --version

# Install with prefer-binary flag
pip install --prefer-binary -r requirements.txt
```

## Still Having Issues?

1. **Clean slate**:
   ```bash
   cd backend
   rm -rf venv
   python3.12 -m venv venv  # Use specific Python version
   source venv/bin/activate
   pip install --upgrade pip
   pip install --prefer-binary -r requirements.txt
   ```

2. **Check logs**:
   ```bash
   pip install -r requirements.txt --verbose
   ```

3. **Minimal install** (just to get started):
   ```bash
   pip install fastapi uvicorn httpx
   python main.py
   ```

## Alternative: Use Docker (Coming Soon)

If you continue having issues, we'll provide a Docker setup that handles all dependencies.
