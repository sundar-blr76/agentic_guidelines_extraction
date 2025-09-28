#!/bin/bash
# Full Application Restart Script
# Kills existing servers, clears logs, and restarts both backend and frontend

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Full Application Restart ===${NC}"
echo "Timestamp: $(date)"

# Function to show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --help, -h        Show this help message"
    echo "  --clear-logs      Clear all log files before restart"
    echo "  --no-frontend     Only restart backend"
    echo "  --no-backend      Only restart frontend"
    echo "  --test            Run basic functionality test after restart"
    echo ""
    echo "Examples:"
    echo "  $0                    # Restart both servers"
    echo "  $0 --clear-logs       # Clear logs and restart"
    echo "  $0 --no-frontend      # Only restart backend"
    echo "  $0 --test             # Restart and run tests"
    exit 0
}

# Parse command line arguments
CLEAR_LOGS=false
START_FRONTEND=true
START_BACKEND=true
RUN_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            ;;
        --clear-logs)
            CLEAR_LOGS=true
            shift
            ;;
        --no-frontend)
            START_FRONTEND=false
            shift
            ;;
        --no-backend)
            START_BACKEND=false
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            ;;
    esac
done

# Step 1: Kill existing processes
echo -e "${YELLOW}Step 1: Stopping existing processes...${NC}"

# Kill backend server (port 8000)
if pgrep -f "uvicorn.*8000" > /dev/null; then
    echo "Killing backend server..."
    pkill -f "uvicorn.*8000" || true
    sleep 2
fi

# Kill frontend server (port 3000 or 3001)
if pgrep -f "node.*react-scripts" > /dev/null; then
    echo "Killing frontend server..."
    pkill -f "node.*react-scripts" || true
    sleep 2
fi

# Clean up any remaining processes
for port in 8000 3000 3001; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "Killing process on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

echo -e "${GREEN}✓ All processes stopped${NC}"

# Step 2: Clear logs if requested
if [ "$CLEAR_LOGS" = true ]; then
    echo -e "${YELLOW}Step 2: Clearing log files...${NC}"
    
    # Clear main log files
    > logs/api_server.log 2>/dev/null || touch logs/api_server.log
    > logs/backend_startup.log 2>/dev/null || touch logs/backend_startup.log
    > logs/frontend_startup.log 2>/dev/null || touch logs/frontend_startup.log
    
    # Remove PID files
    rm -f logs/backend.pid logs/frontend.pid
    
    echo -e "${GREEN}✓ Log files cleared${NC}"
else
    echo -e "${YELLOW}Step 2: Keeping existing logs${NC}"
fi

# Step 3: Ensure logs directory exists and create PID files location
mkdir -p logs

# Step 4: Start Backend Server
if [ "$START_BACKEND" = true ]; then
    echo -e "${YELLOW}Step 3: Starting backend server...${NC}"
    
    # Activate virtual environment and start backend
    nohup bash -c '
        source venv/bin/activate
        python -m uvicorn guidelines_agent.main:app --host 0.0.0.0 --port 8000 --reload
    ' > logs/backend_startup.log 2>&1 &
    
    BACKEND_PID=$!
    echo $BACKEND_PID > logs/backend.pid
    
    # Wait for backend to start
    echo "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend server started (PID: $BACKEND_PID)${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ Backend failed to start within 30 seconds${NC}"
            echo "Check logs/backend_startup.log for details"
            exit 1
        fi
        sleep 1
    done
fi

# Step 5: Start Frontend Server
if [ "$START_FRONTEND" = true ]; then
    echo -e "${YELLOW}Step 4: Starting frontend server...${NC}"
    
    # Start frontend
    cd frontend
    nohup bash -c '
        npm start
    ' > ../logs/frontend_startup.log 2>&1 &
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    cd ..
    
    # Wait for frontend to start
    echo "Waiting for frontend to start..."
    for i in {1..60}; do
        # Check for any React server on ports 3000-3010
        if lsof -i :3000 >/dev/null 2>&1 || lsof -i :3001 >/dev/null 2>&1 || lsof -i :3002 >/dev/null 2>&1; then
            FRONTEND_PORT=$(lsof -ti:3000,3001,3002 | head -1 | xargs -I {} lsof -Pan -p {} -i | grep LISTEN | sed 's/.*:\([0-9]*\).*/\1/' | head -1)
            echo -e "${GREEN}✓ Frontend server started on port ${FRONTEND_PORT:-3000} (PID: $FRONTEND_PID)${NC}"
            break
        fi
        if [ $i -eq 60 ]; then
            echo -e "${RED}✗ Frontend failed to start within 60 seconds${NC}"
            echo "Check logs/frontend_startup.log for details"
        fi
        sleep 1
    done
fi

# Step 6: Show status
echo -e "${BLUE}=== Server Status ===${NC}"
if [ "$START_BACKEND" = true ]; then
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend:  http://localhost:8000 (Running)${NC}"
    else
        echo -e "${RED}✗ Backend:  http://localhost:8000 (Not responding)${NC}"
    fi
fi

if [ "$START_FRONTEND" = true ]; then
    if lsof -i :3000 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend: http://localhost:3000 (Running)${NC}"
    elif lsof -i :3001 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend: http://localhost:3001 (Running)${NC}"
    elif lsof -i :3002 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend: http://localhost:3002 (Running)${NC}"
    else
        echo -e "${RED}✗ Frontend: Not running on expected ports${NC}"
    fi
fi

echo ""
echo "Log files:"
echo "  Backend:  logs/api_server.log"
echo "  Startup:  logs/backend_startup.log, logs/frontend_startup.log"
echo ""
echo "To stop servers: pkill -f 'uvicorn.*8000' && pkill -f 'node.*react-scripts'"

# Step 7: Run basic functionality tests
if [ "$RUN_TESTS" = true ]; then
    echo -e "${YELLOW}Step 5: Running functionality tests...${NC}"
    
    if [ "$START_BACKEND" = true ]; then
        echo "Testing backend health endpoint..."
        if curl -s http://localhost:8000/health | grep -q "healthy"; then
            echo -e "${GREEN}✓ Backend health check passed${NC}"
            
            # Test document ingestion if test file exists
            if [ -f "test_guidelines.pdf" ]; then
                echo "Testing document ingestion..."
                RESPONSE=$(curl -s -X POST "http://localhost:8000/agent/ingest" \
                    -H "Content-Type: multipart/form-data" \
                    -F "file=@test_guidelines.pdf" \
                    -F "session_id=test-restart-$(date +%s)" \
                    --max-time 120)
                
                if echo "$RESPONSE" | grep -q "success.*true"; then
                    echo -e "${GREEN}✓ Document ingestion test passed${NC}"
                else
                    echo -e "${RED}✗ Document ingestion test failed${NC}"
                    echo "Response: $RESPONSE"
                fi
            fi
        else
            echo -e "${RED}✗ Backend health check failed${NC}"
        fi
    fi
fi

echo -e "${GREEN}=== Restart Complete ===${NC}"