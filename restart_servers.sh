#!/bin/bash
# Comprehensive restart script for both frontend and backend servers
# Handles existing processes, log cleanup, and health verification

set -e

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
LOG_FILE="logs/api_server.log"
BACKEND_LOG="logs/backend_startup.log"
FRONTEND_LOG="logs/frontend_startup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pids" ]; then
        log_warn "Killing existing $service_name processes on port $port"
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 2
        
        # Verify processes are killed
        local remaining=$(lsof -ti:$port 2>/dev/null || true)
        if [ ! -z "$remaining" ]; then
            log_error "Failed to kill some $service_name processes, trying again..."
            echo $remaining | xargs kill -9 2>/dev/null || true
            sleep 1
        fi
        log_info "$service_name processes killed successfully"
    else
        log_info "No existing $service_name processes found on port $port"
    fi
}

# Function to kill processes by name pattern
kill_by_pattern() {
    local pattern=$1
    local service_name=$2
    
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [ ! -z "$pids" ]; then
        log_warn "Killing $service_name processes matching: $pattern"
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 1
        log_info "$service_name processes killed successfully"
    fi
}

# Function to clear and setup log files
setup_logs() {
    log_step "Setting up log files..."
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Clear main API server log
    > "$LOG_FILE"
    log_info "Cleared main API server log: $LOG_FILE"
    
    # Clear or create startup logs
    > "$BACKEND_LOG"
    > "$FRONTEND_LOG"
    log_info "Cleared startup logs: $BACKEND_LOG, $FRONTEND_LOG"
    
    # Set proper permissions
    chmod 644 logs/*.log 2>/dev/null || true
}

# Function to start backend server
start_backend() {
    log_step "Starting backend server..."
    
    # Kill any existing backend processes
    kill_port $BACKEND_PORT "Backend"
    kill_by_pattern "uvicorn.*guidelines_agent" "Uvicorn"
    
    # Activate virtual environment and start server
    if [ -f "venv/bin/activate" ]; then
        log_info "Activating virtual environment..."
        source venv/bin/activate
    else
        log_warn "Virtual environment not found, using system Python"
    fi
    
    # Set environment variables for centralized caching
    export PYTHONPYCACHEPREFIX=.build_cache/pycache
    export PYTEST_CACHE_DIR=.build_cache/pytest
    export RUFF_CACHE_DIR=.build_cache/ruff
    
    log_info "Starting backend server on port $BACKEND_PORT..."
    
    # Start backend server in background
    nohup python3 -m uvicorn guidelines_agent.main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --reload \
        > "$BACKEND_LOG" 2>&1 &
    
    local backend_pid=$!
    echo $backend_pid > logs/backend.pid
    log_info "Backend server started with PID: $backend_pid"
    
    # Wait for backend to be ready
    log_info "Waiting for backend to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s --max-time 2 "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1; then
            log_info "✅ Backend server is ready and healthy!"
            return 0
        fi
        
        if [ $((attempt % 5)) -eq 0 ]; then
            log_info "Still waiting for backend... (attempt $attempt/$max_attempts)"
        fi
        
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_error "❌ Backend server failed to start within ${max_attempts} seconds"
    log_error "Check logs: $BACKEND_LOG"
    tail -10 "$BACKEND_LOG" 2>/dev/null || true
    return 1
}

# Function to start frontend server
start_frontend() {
    log_step "Starting frontend server..."
    
    # Kill any existing frontend processes
    kill_port $FRONTEND_PORT "Frontend"
    kill_by_pattern "node.*react-scripts" "React"
    kill_by_pattern "npm.*start" "NPM"
    
    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        log_error "Frontend directory not found!"
        return 1
    fi
    
    # Check if node_modules exists
    if [ ! -d "frontend/node_modules" ]; then
        log_warn "node_modules not found, installing dependencies..."
        cd frontend && npm install && cd ..
    fi
    
    log_info "Starting frontend server on port $FRONTEND_PORT..."
    
    # Start frontend server in background
    cd frontend
    nohup npm start > "../$FRONTEND_LOG" 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > ../logs/frontend.pid
    cd ..
    
    log_info "Frontend server started with PID: $frontend_pid"
    
    # Wait for frontend to be ready
    log_info "Waiting for frontend to be ready..."
    local max_attempts=60  # Frontend takes longer to start
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s --max-time 2 "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
            log_info "✅ Frontend server is ready!"
            return 0
        fi
        
        if [ $((attempt % 10)) -eq 0 ]; then
            log_info "Still waiting for frontend... (attempt $attempt/$max_attempts)"
        fi
        
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_warn "⚠️  Frontend server may still be starting (timeout reached)"
    log_info "Check logs: $FRONTEND_LOG"
    return 0  # Don't fail the script for frontend timeout
}

# Function to verify both servers
verify_servers() {
    log_step "Verifying server status..."
    
    local backend_ok=false
    local frontend_ok=false
    
    # Check backend
    if curl -s --max-time 5 "http://localhost:$BACKEND_PORT/health" | grep -q "healthy"; then
        log_info "✅ Backend API: http://localhost:$BACKEND_PORT - HEALTHY"
        backend_ok=true
    else
        log_error "❌ Backend API: http://localhost:$BACKEND_PORT - NOT RESPONDING"
    fi
    
    # Check frontend
    if curl -s --max-time 5 "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        log_info "✅ Frontend UI: http://localhost:$FRONTEND_PORT - ACCESSIBLE"
        frontend_ok=true
    else
        log_warn "⚠️  Frontend UI: http://localhost:$FRONTEND_PORT - NOT READY YET"
    fi
    
    # Test API integration
    if [ "$backend_ok" = true ]; then
        log_info "Testing API endpoints..."
        
        # Test session creation
        if curl -s -X POST "http://localhost:$BACKEND_PORT/sessions" \
           -H "Content-Type: application/json" -d '{}' | grep -q "session_id"; then
            log_info "✅ Session creation: Working"
        else
            log_error "❌ Session creation: Failed"
        fi
        
        # Test chat endpoint
        if curl -s -X POST "http://localhost:$BACKEND_PORT/agent/chat" \
           -H "Content-Type: application/json" -d '{"message":"test"}' | grep -q "response"; then
            log_info "✅ Chat endpoint: Working"
        else
            log_error "❌ Chat endpoint: Failed"
        fi
    fi
}

# Function to show running processes
show_processes() {
    log_step "Current server processes..."
    
    echo "Backend processes:"
    pgrep -f "uvicorn.*guidelines_agent" 2>/dev/null | while read pid; do
        echo "  PID $pid: $(ps -p $pid -o command --no-headers 2>/dev/null || echo 'Process not found')"
    done || echo "  No backend processes found"
    
    echo "Frontend processes:"
    pgrep -f "node.*react-scripts\|npm.*start" 2>/dev/null | while read pid; do
        echo "  PID $pid: $(ps -p $pid -o command --no-headers 2>/dev/null | cut -c1-80)..."
    done || echo "  No frontend processes found"
    
    echo "Port usage:"
    echo "  Backend port $BACKEND_PORT: $(lsof -ti:$BACKEND_PORT 2>/dev/null | wc -l) process(es)"
    echo "  Frontend port $FRONTEND_PORT: $(lsof -ti:$FRONTEND_PORT 2>/dev/null | wc -l) process(es)"
}

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Restart both frontend and backend servers with proper cleanup."
    echo ""
    echo "Options:"
    echo "  --backend-only    Start only backend server"
    echo "  --frontend-only   Start only frontend server"
    echo "  --kill-only       Kill servers without restarting"
    echo "  --status          Show current server status"
    echo "  --logs            Show recent log files"
    echo "  --help            Show this help message"
    echo ""
    echo "Default: Restart both servers with log cleanup"
}

# Function to show logs
show_logs() {
    log_step "Recent log files..."
    
    if [ -f "$LOG_FILE" ]; then
        echo "=== API Server Log (last 20 lines) ==="
        tail -20 "$LOG_FILE" 2>/dev/null || echo "Log file is empty"
        echo ""
    fi
    
    if [ -f "$BACKEND_LOG" ]; then
        echo "=== Backend Startup Log (last 10 lines) ==="
        tail -10 "$BACKEND_LOG" 2>/dev/null || echo "Log file is empty"
        echo ""
    fi
    
    if [ -f "$FRONTEND_LOG" ]; then
        echo "=== Frontend Startup Log (last 10 lines) ==="
        tail -10 "$FRONTEND_LOG" 2>/dev/null || echo "Log file is empty"
    fi
}

# Main execution
main() {
    echo "🚀 Guidelines Agent Server Restart Script"
    echo "========================================"
    
    local backend_only=false
    local frontend_only=false
    local kill_only=false
    local show_status=false
    local show_log_files=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                backend_only=true
                shift
                ;;
            --frontend-only)
                frontend_only=true
                shift
                ;;
            --kill-only)
                kill_only=true
                shift
                ;;
            --status)
                show_status=true
                shift
                ;;
            --logs)
                show_log_files=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Handle special modes
    if [ "$show_status" = true ]; then
        show_processes
        echo ""
        verify_servers
        exit 0
    fi
    
    if [ "$show_log_files" = true ]; then
        show_logs
        exit 0
    fi
    
    if [ "$kill_only" = true ]; then
        log_step "Killing all server processes..."
        kill_port $BACKEND_PORT "Backend"
        kill_port $FRONTEND_PORT "Frontend"
        kill_by_pattern "uvicorn.*guidelines_agent" "Uvicorn"
        kill_by_pattern "node.*react-scripts\|npm.*start" "Frontend"
        log_info "All servers stopped"
        exit 0
    fi
    
    # Setup logs first
    setup_logs
    
    # Start servers based on options
    if [ "$frontend_only" = true ]; then
        start_frontend
    elif [ "$backend_only" = true ]; then
        start_backend
    else
        # Start both servers (default)
        start_backend
        if [ $? -eq 0 ]; then
            start_frontend
        else
            log_error "Backend failed to start, skipping frontend"
            exit 1
        fi
    fi
    
    echo ""
    verify_servers
    echo ""
    show_processes
    
    echo ""
    echo "🎉 Server restart completed!"
    echo "================================"
    echo "📱 Frontend: http://localhost:$FRONTEND_PORT"
    echo "🔧 Backend API: http://localhost:$BACKEND_PORT"
    echo "📚 API Docs: http://localhost:$BACKEND_PORT/docs"
    echo "📋 Logs: $LOG_FILE"
    echo ""
    echo "Use '$0 --status' to check server status"
    echo "Use '$0 --logs' to view recent logs"
    echo "Use '$0 --kill-only' to stop all servers"
}

# Handle Ctrl+C gracefully
trap 'echo ""; log_warn "Script interrupted by user"; exit 130' INT

# Run main function with all arguments
main "$@"