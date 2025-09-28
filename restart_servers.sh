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
    echo "🚀 Comprehensive server management for Guidelines Agent application."
    echo "   Handles both frontend (React) and backend (FastAPI) servers with"
    echo "   automatic process cleanup, log clearing, and health verification."
    echo ""
    echo "📋 OPTIONS:"
    echo "  --backend-only    Start only backend server (FastAPI on port 8000)"
    echo "  --frontend-only   Start only frontend server (React on port 3000)"
    echo "  --kill-only       Kill all servers without restarting"
    echo "  --status          Show current server status and running processes"
    echo "  --logs            Show recent log files content"
    echo "  --help            Show this detailed help message"
    echo ""
    echo "🎯 USAGE EXAMPLES:"
    echo ""
    echo "  # 🔄 Full restart (most common - restarts both servers)"
    echo "  $0"
    echo ""
    echo "  # ⚡ Backend development (API changes only)"
    echo "  $0 --backend-only"
    echo ""
    echo "  # 🎨 Frontend development (UI changes only)"
    echo "  $0 --frontend-only"
    echo ""
    echo "  # 📊 Check what's currently running"
    echo "  $0 --status"
    echo ""
    echo "  # 📋 Debug issues with recent logs"
    echo "  $0 --logs"
    echo ""
    echo "  # 🛑 Clean shutdown (stop all servers)"
    echo "  $0 --kill-only"
    echo ""
    echo "🌟 WHAT THIS SCRIPT DOES:"
    echo "  ✅ Kills existing processes on ports 8000 and 3000"
    echo "  ✅ Clears all log files (logs/api_server.log, startup logs)"
    echo "  ✅ Starts servers with proper virtual environment"
    echo "  ✅ Waits for servers to be ready (health checks)"
    echo "  ✅ Verifies API endpoints are working"
    echo "  ✅ Shows process status and diagnostics"
    echo "  ✅ Provides colored output for easy reading"
    echo ""
    echo "🚀 DEVELOPMENT WORKFLOW:"
    echo "  Daily development:     $0 --backend-only    # Fast backend restart"
    echo "  After major changes:   $0                   # Full verification restart"
    echo "  UI/Frontend work:      $0 --frontend-only   # Frontend only"
    echo "  Check if working:      $0 --status          # Status check"
    echo "  Debug problems:        $0 --logs            # View recent logs"
    echo "  Clean shutdown:        $0 --kill-only       # Stop everything"
    echo ""
    echo "📚 SERVER INFORMATION:"
    echo "  Backend API:     http://localhost:8000"
    echo "  API Docs:        http://localhost:8000/docs"
    echo "  Frontend UI:     http://localhost:3000"
    echo "  Health Check:    http://localhost:8000/health"
    echo ""
    echo "📋 LOG FILES:"
    echo "  Main API log:    logs/api_server.log"
    echo "  Backend startup: logs/backend_startup.log"
    echo "  Frontend startup: logs/frontend_startup.log"
    echo ""
    echo "🛠️  TROUBLESHOOTING:"
    echo "  If servers won't start:"
    echo "    1. $0 --kill-only     # Force stop all processes"
    echo "    2. $0 --logs          # Check for error messages"  
    echo "    3. $0 --backend-only  # Try backend first"
    echo "    4. Check ports: lsof -i:8000 && lsof -i:3000"
    echo ""
    echo "💡 TIP: Use './quick_restart.sh' for fast daily restarts without verification"
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
    echo "=========================================="
    echo "💡 Starting comprehensive server management..."
    echo "   Backend (FastAPI): Port $BACKEND_PORT"
    echo "   Frontend (React):  Port $FRONTEND_PORT" 
    echo "   Log clearing:      Enabled"
    echo "   Health checks:     Enabled"
    echo ""
    
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
    echo "🌐 SERVERS RUNNING:"
    echo "📱 Frontend UI:   http://localhost:$FRONTEND_PORT"
    echo "🔧 Backend API:   http://localhost:$BACKEND_PORT"  
    echo "📚 API Docs:      http://localhost:$BACKEND_PORT/docs"
    echo "💓 Health Check:  http://localhost:$BACKEND_PORT/health"
    echo ""
    echo "📋 LOG FILES:"
    echo "📝 Main API Log:  $LOG_FILE"
    echo "🚀 Backend Log:   $BACKEND_LOG" 
    echo "⚛️  Frontend Log:  $FRONTEND_LOG"
    echo ""
    echo "🛠️  MANAGEMENT COMMANDS:"
    echo "📊 Check Status:  $0 --status"
    echo "📋 View Logs:     $0 --logs" 
    echo "🛑 Stop Servers:  $0 --kill-only"
    echo "⚡ Quick Restart: ./quick_restart.sh"
    echo ""
    echo "💡 TIP: Open http://localhost:3000 in your browser to use the chat interface!"
}

# Handle Ctrl+C gracefully
trap 'echo ""; log_warn "Script interrupted by user"; exit 130' INT

# Run main function with all arguments
main "$@"