#!/bin/bash
# Quick test runner - runs regression tests with server check

echo "🚀 Quick API Regression Test"
echo "============================="

# Check if server is running
if ! curl -s --max-time 3 http://localhost:8000/health > /dev/null; then
    echo "⚠️  Starting server..."
    ./start_server.sh &
    SERVER_PID=$!
    sleep 10
    
    if ! curl -s --max-time 3 http://localhost:8000/health > /dev/null; then
        echo "❌ Could not start server"
        exit 1
    fi
    echo "✅ Server started"
else
    echo "✅ Server already running"
fi

# Run regression tests
echo ""
echo "🧪 Running regression tests..."
python3 tests/integration/test_api_regression.py

echo ""
echo "🏁 Test completed!"