#!/bin/bash

# ==============================================================================
# Application Server Restart Script
# ==============================================================================
# This script manages both frontend and backend servers for the Agentic 
# Guidelines Extraction application.
#
# Features:
# - Kills existing server processes
# - Clears log files
# - Starts both frontend and backend servers
# - Provides usage information and status checking
#
# Usage:
#   ./restart_application.sh [options]
#
# Options:
#   --help, -h          Show this help message
#   --status, -s        Show server status only
#   --backend-only      Restart only the backend server
#   --frontend-only     Restart only the frontend server
#   --no-logs           Don't clear log files
#   --verbose, -v       Enable verbose output
#
# Examples:
#   ./restart_application.sh                 # Restart both servers
#   ./restart_application.sh --status        # Check server status
#   ./restart_application.sh --backend-only  # Restart backend only
# ==============================================================================

set -e  # Exit on any error

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_PORT="8000"
FRONTEND_PORT="3000"
VERBOSE=false
CLEAR_LOGS=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Show usage information
show_usage() {
    cat << EOF
Agentic Guidelines Extraction - Server Management

USAGE:
    $0 [options]

OPTIONS:
    --help, -h          Show this help message
    --status, -s        Show server status only  
    --backend-only      Restart only the backend server
    --frontend-only     Restart only the frontend server
    --no-logs           Don't clear log files
    --verbose, -v       Enable verbose output

EXAMPLES:
    $0                        # Restart both servers
    $0 --status               # Check server status
    $0 --backend-only         # Restart backend only
    $0 --frontend-only        # Restart frontend only
    $0 --no-logs --verbose    # Restart without clearing logs, verbose output

DESCRIPTION:
    This script manages the frontend (React) and backend (FastAPI) servers
    for the Agentic Guidelines Extraction application.
    
    It will:
    1. Kill any existing server processes
    2. Clear log files (unless --no-logs is specified)
    3. Start the specified servers
    4. Show server status and access URLs

PORTS:
    Backend:  http://localhost:$BACKEND_PORT
    Frontend: http://localhost:$FRONTEND_PORT

LOG FILES:
    Backend:  $LOGS_DIR/api_server.log
    Frontend: $LOGS_DIR/frontend_startup.log
    PIDs:     $LOGS_DIR/backend.pid, $LOGS_DIR/frontend.pid

EOF
}

# Check if a process is running on a specific port
check_port() {
    local port=$1
    local process=$(lsof -ti:$port 2>/dev/null || echo "")
    if [ -n "$process" ]; then
        echo "$process"
    else
        echo ""
    fi
}

# Get process info from PID file
get_pid_info() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file" 2>/dev/null || echo "")
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
        else
            echo ""
        fi
    else
        echo ""
    fi
}

# Show server status
show_status() {
    log_info "Checking server status..."
    echo
    
    # Backend status
    local backend_pid=$(get_pid_info "$LOGS_DIR/backend.pid")
    local backend_port_pid=$(check_port $BACKEND_PORT)
    
    echo -e "${BLUE}Backend Server (Port $BACKEND_PORT):${NC}"
    if [ -n "$backend_pid" ] && [ -n "$backend_port_pid" ]; then
        echo -e "  Status: ${GREEN}RUNNING${NC} (PID: $backend_pid)"
        echo -e "  URL: ${BLUE}http://localhost:$BACKEND_PORT${NC}"
        echo -e "  Health: ${BLUE}http://localhost:$BACKEND_PORT/health${NC}"
    elif [ -n "$backend_port_pid" ]; then
        echo -e "  Status: ${YELLOW}RUNNING${NC} (PID: $backend_port_pid, not managed by this script)"
    else
        echo -e "  Status: ${RED}STOPPED${NC}"
    fi
    
    # Frontend status  
    local frontend_pid=$(get_pid_info "$LOGS_DIR/frontend.pid")
    local frontend_port_pid=$(check_port $FRONTEND_PORT)
    
    echo -e "${BLUE}Frontend Server (Port $FRONTEND_PORT):${NC}"
    if [ -n "$frontend_pid" ] && [ -n "$frontend_port_pid" ]; then
        echo -e "  Status: ${GREEN}RUNNING${NC} (PID: $frontend_pid)"
        echo -e "  URL: ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
    elif [ -n "$frontend_port_pid" ]; then
        echo -e "  Status: ${YELLOW}RUNNING${NC} (PID: $frontend_port_pid, not managed by this script)"
    else
        echo -e "  Status: ${RED}STOPPED${NC}"
    fi
    
    echo
    
    # Log file status
    echo -e "${BLUE}Log Files:${NC}"
    for log_file in "$LOGS_DIR/api_server.log" "$LOGS_DIR/frontend_startup.log"; do
        if [ -f "$log_file" ]; then
            local size=$(du -h "$log_file" | cut -f1)
            local lines=$(wc -l < "$log_file")
            echo "  $(basename "$log_file"): $size ($lines lines)"
        else
            echo "  $(basename "$log_file"): Not found"
        fi
    done
}

# Kill process by PID file
kill_by_pid_file() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file" 2>/dev/null || echo "")
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            log_debug "Killing $service_name process (PID: $pid)"
            kill -TERM "$pid" 2>/dev/null || true
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                log_warn "Process $pid didn't respond to TERM, using KILL"
                kill -KILL "$pid" 2>/dev/null || true
            fi
            log_info "Stopped $service_name (PID: $pid)"
        fi
        rm -f "$pid_file"
    fi
}

# Kill process by port
kill_by_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti:$port 2>/dev/null || echo "")
    if [ -n "$pids" ]; then
        log_debug "Killing processes on port $port: $pids"
        echo "$pids" | xargs -r kill -TERM 2>/dev/null || true
        sleep 2
        
        # Check if any processes are still running
        local remaining=$(lsof -ti:$port 2>/dev/null || echo "")
        if [ -n "$remaining" ]; then
            log_warn "Some processes on port $port didn't respond to TERM, using KILL"
            echo "$remaining" | xargs -r kill -KILL 2>/dev/null || true
        fi
        log_info "Stopped $service_name processes on port $port"
    fi
}

# Stop backend server
stop_backend() {
    log_debug "Stopping backend server..."
    kill_by_pid_file "$LOGS_DIR/backend.pid" "backend server"
    kill_by_port "$BACKEND_PORT" "backend server"
}

# Stop frontend server
stop_frontend() {
    log_debug "Stopping frontend server..."
    kill_by_pid_file "$LOGS_DIR/frontend.pid" "frontend server"
    kill_by_port "$FRONTEND_PORT" "frontend server"
}

# Clear log files
clear_logs() {
    if [ "$CLEAR_LOGS" = true ]; then
        log_debug "Clearing log files..."
        mkdir -p "$LOGS_DIR"
        > "$LOGS_DIR/api_server.log"
        > "$LOGS_DIR/frontend_startup.log"
        log_info "Log files cleared"
    fi
}

# Start backend server
start_backend() {
    log_info "Starting backend server..."
    
    cd "$PROJECT_ROOT"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log_error "Python virtual environment not found. Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        return 1
    fi
    
    # Activate virtual environment and start server
    nohup bash -c "
        source venv/bin/activate && \
        python -m uvicorn guidelines_agent.main:app \
            --host 0.0.0.0 \
            --port $BACKEND_PORT \
            --reload
    " > "$LOGS_DIR/api_server.log" 2>&1 &
    
    local pid=$!
    echo "$pid" > "$LOGS_DIR/backend.pid"
    
    log_debug "Backend server started with PID: $pid"
    
    # Wait a bit and check if it's running
    sleep 3
    if kill -0 "$pid" 2>/dev/null; then
        log_info "Backend server started successfully (PID: $pid)"
        log_info "Backend URL: http://localhost:$BACKEND_PORT"
        log_info "API Documentation: http://localhost:$BACKEND_PORT/docs"
    else
        log_error "Backend server failed to start"
        return 1
    fi
}

# Start frontend server
start_frontend() {
    log_info "Starting frontend server..."
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_error "Frontend dependencies not found. Please run: cd frontend && npm install"
        return 1
    fi
    
    # Start frontend server
    nohup npm start > "$LOGS_DIR/frontend_startup.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$LOGS_DIR/frontend.pid"
    
    log_debug "Frontend server started with PID: $pid"
    
    # Wait a bit and check if it's running
    sleep 5
    if kill -0 "$pid" 2>/dev/null; then
        log_info "Frontend server started successfully (PID: $pid)"
        log_info "Frontend URL: http://localhost:$FRONTEND_PORT"
    else
        log_error "Frontend server failed to start"
        return 1
    fi
}

# Main restart function
restart_servers() {
    local restart_backend=$1
    local restart_frontend=$2
    
    log_info "Restarting application servers..."
    
    # Stop servers
    if [ "$restart_backend" = true ]; then
        stop_backend
    fi
    
    if [ "$restart_frontend" = true ]; then
        stop_frontend
    fi
    
    # Clear logs
    clear_logs
    
    # Wait a moment for processes to fully terminate
    sleep 2
    
    # Start servers
    local backend_success=true
    local frontend_success=true
    
    if [ "$restart_backend" = true ]; then
        start_backend || backend_success=false
    fi
    
    if [ "$restart_frontend" = true ]; then
        start_frontend || frontend_success=false
    fi
    
    echo
    log_info "Restart complete!"
    
    # Show final status
    show_status
    
    if [ "$backend_success" = false ] || [ "$frontend_success" = false ]; then
        echo
        log_error "Some servers failed to start. Check the logs for details:"
        log_error "  Backend log: $LOGS_DIR/api_server.log"
        log_error "  Frontend log: $LOGS_DIR/frontend_startup.log"
        return 1
    fi
}

# Parse command line arguments
RESTART_BACKEND=true
RESTART_FRONTEND=true
STATUS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            exit 0
            ;;
        --status|-s)
            STATUS_ONLY=true
            shift
            ;;
        --backend-only)
            RESTART_FRONTEND=false
            shift
            ;;
        --frontend-only)
            RESTART_BACKEND=false
            shift
            ;;
        --no-logs)
            CLEAR_LOGS=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# Main execution
if [ "$STATUS_ONLY" = true ]; then
    show_status
else
    restart_servers "$RESTART_BACKEND" "$RESTART_FRONTEND"
fi