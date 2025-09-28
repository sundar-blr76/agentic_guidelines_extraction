#!/bin/bash
# Start the server with centralized caching
export PYTHONPYCACHEPREFIX=.build_cache/pycache
export PYTEST_CACHE_DIR=.build_cache/pytest  
export RUFF_CACHE_DIR=.build_cache/ruff

echo "🚀 Starting server with centralized caching..."
echo "📁 Python cache: .build_cache/pycache/"
echo "📁 Pytest cache: .build_cache/pytest/"
echo "📁 Ruff cache: .build_cache/ruff/"

python3 -m uvicorn guidelines_agent.main:app --host 0.0.0.0 --port 8000 --reload