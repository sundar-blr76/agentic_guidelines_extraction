#!/bin/bash

# Enhanced Restart Script for Guidelines Agent
# Kills existing servers, clears logs, and starts fresh

echo "🔄 Restarting Guidelines Agent Application..."

# Function to get script usage
show_usage() {
    echo ""
    echo "📋 USAGE:"
    echo "  ./restart_with_clean_logs.sh [options]"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Show detailed output"
    echo ""
    echo "FUNCTIONALITY:"
    echo "  1. Kills existing backend and frontend processes"
    echo "  2. Clears all log files"
    echo "  3. Starts the backend server (port 8000)"
    echo "  4. Starts the frontend development server (port 3000)"
    echo ""
    echo "ENDPOINTS AFTER START:"
    echo "  🔗 Frontend:  http://localhost:3000"
    echo "  🔗 Backend:   http://localhost:8000"
    echo "  🔗 API Docs:  http://localhost:8000/docs"
    echo ""
}

VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Set up directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Function to log with timestamp
log_message() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $message"
    if [ "$VERBOSE" = true ]; then
        echo "  ℹ️  Location: $SCRIPT_DIR"
    fi
}

# Step 1: Kill existing processes
log_message "🛑 Stopping existing processes..."

# Kill backend (FastAPI/uvicorn on port 8000)
backend_pids=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$backend_pids" ]; then
    echo "$backend_pids" | xargs kill -9 2>/dev/null || true
    log_message "✅ Killed backend processes: $backend_pids"
else
    log_message "ℹ️  No backend processes found on port 8000"
fi

# Kill frontend (React dev server on port 3000)
frontend_pids=$(lsof -ti:3000 2>/dev/null || true)
if [ ! -z "$frontend_pids" ]; then
    echo "$frontend_pids" | xargs kill -9 2>/dev/null || true
    log_message "✅ Killed frontend processes: $frontend_pids"
else
    log_message "ℹ️  No frontend processes found on port 3000"
fi

# Wait a moment for processes to terminate
sleep 2

# Step 2: Clear log files
log_message "🧹 Clearing log files..."

# Clear API server logs
if [ -f "$LOGS_DIR/api_server.log" ]; then
    > "$LOGS_DIR/api_server.log"
    log_message "✅ Cleared api_server.log"
fi

# Clear frontend logs
if [ -f "$LOGS_DIR/frontend.log" ]; then
    > "$LOGS_DIR/frontend.log"
    log_message "✅ Cleared frontend.log"
fi

# Clear any other log files
for log_file in "$LOGS_DIR"/*.log; do
    if [ -f "$log_file" ] && [[ "$log_file" != *"api_server.log" ]] && [[ "$log_file" != *"frontend.log" ]]; then
        > "$log_file"
        log_message "✅ Cleared $(basename "$log_file")"
    fi
done

# Step 3: Start backend server
log_message "🚀 Starting backend server..."

cd "$SCRIPT_DIR"

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    source venv/bin/activate
    log_message "✅ Activated virtual environment"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    log_message "✅ Activated virtual environment (.venv)"
else
    log_message "⚠️  No virtual environment found - using system Python"
fi

# Start backend in background
nohup python -m uvicorn guidelines_agent.main:app --host 0.0.0.0 --port 8000 --reload > "$LOGS_DIR/api_server.log" 2>&1 &
backend_pid=$!
log_message "🟢 Backend started (PID: $backend_pid) - Logs: $LOGS_DIR/api_server.log"

# Wait for backend to initialize
sleep 3

# Test backend health
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    log_message "✅ Backend health check passed"
else
    log_message "⚠️  Backend health check failed - check logs"
fi

# Step 4: Start frontend server
log_message "🚀 Starting frontend server..."

if [ -d "$SCRIPT_DIR/frontend" ]; then
    cd "$SCRIPT_DIR/frontend"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_message "📦 Installing frontend dependencies..."
        npm install
    fi
    
    # Start frontend in background
    nohup npm start > "$LOGS_DIR/frontend.log" 2>&1 &
    frontend_pid=$!
    log_message "🟢 Frontend started (PID: $frontend_pid) - Logs: $LOGS_DIR/frontend.log"
    
    # Wait for frontend to initialize
    sleep 5
    
    # Test frontend
    if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
        log_message "✅ Frontend health check passed"
    else
        log_message "⚠️  Frontend health check failed - may still be starting"
    fi
    
else
    log_message "⚠️  Frontend directory not found - skipping frontend startup"
fi

# Final status
log_message "🎉 Application restart completed!"
echo ""
echo "🌐 AVAILABLE SERVICES:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000" 
echo "  API Docs:  http://localhost:8000/docs"
echo "  Health:    http://localhost:8000/health"
echo ""
echo "📝 LOG FILES:"
echo "  Backend:   $LOGS_DIR/api_server.log"
echo "  Frontend:  $LOGS_DIR/frontend.log"
echo ""
echo "🔍 Monitor logs with:"
echo "  tail -f $LOGS_DIR/api_server.log"
echo "  tail -f $LOGS_DIR/frontend.log"
echo ""

if [ "$VERBOSE" = true ]; then
    echo "🔧 PROCESS IDs:"
    echo "  Backend PID:  $backend_pid"
    echo "  Frontend PID: $frontend_pid"
    echo ""
fi

echo "✨ Ready for testing!"