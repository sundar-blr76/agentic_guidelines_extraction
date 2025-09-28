#!/bin/bash
# Set Python to use centralized cache directory
export PYTHONPYCACHEPREFIX=.build_cache/pycache

# Set other build caches to centralized location
export PYTEST_CACHE_DIR=.build_cache/pytest
export RUFF_CACHE_DIR=.build_cache/ruff

# Run the command with centralized caching
exec "$@"