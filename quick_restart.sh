#!/bin/bash
# 🚀 Quick Server Restart - Fast daily development restarts
# 
# USAGE:
#   ./quick_restart.sh                    # Fast restart both servers
#   ./quick_restart.sh --help             # Show this help
#
# FEATURES:
#   ⚡ Fast execution (no health checks or waiting)
#   🧹 Clears main API log file
#   🔄 Starts both servers in background
#   📊 Basic server availability check
#
# FOR COMPREHENSIVE RESTART WITH VERIFICATION:
#   Use ./restart_servers.sh instead
#
# SERVERS:
#   Backend:  http://localhost:8000 (API + Docs)
#   Frontend: http://localhost:3000 (Chat Interface)

if [ "$1" = "--help" ]; then
    echo "🚀 Quick Server Restart"
    echo "======================"
    echo ""
    echo "Fast restart script for daily development workflow."
    echo ""
    echo "Usage:"
    echo "  $0                    # Quick restart both servers"
    echo "  $0 --help             # Show this help message"
    echo ""
    echo "What it does:"
    echo "  ✅ Kills existing server processes"
    echo "  ✅ Clears main API log file"
    echo "  ✅ Starts backend server (FastAPI on port 8000)"
    echo "  ✅ Starts frontend server (React on port 3000)"
    echo "  ✅ Quick availability check"
    echo ""
    echo "For full restart with health checks and verification:"
    echo "  ./restart_servers.sh"
    echo ""
    echo "To check server status after restart:"
    echo "  ./restart_servers.sh --status"
    echo ""
    echo "Servers will be available at:"
    echo "  🌐 Frontend: http://localhost:3000"
    echo "  🔧 API:      http://localhost:8000"
    echo "  📚 Docs:     http://localhost:8000/docs"
    exit 0
fi

echo "🔄 Quick Server Restart..."
echo "========================="

# Kill existing processes
pkill -f "uvicorn.*guidelines_agent" 2>/dev/null || true
pkill -f "npm.*start\|node.*react-scripts" 2>/dev/null || true

# Clear logs
> logs/api_server.log 2>/dev/null || mkdir -p logs && > logs/api_server.log

echo "⏳ Starting servers..."

# Start backend
source venv/bin/activate 2>/dev/null || true
nohup ./start_server.sh > logs/backend_startup.log 2>&1 &

# Start frontend
cd frontend && nohup npm start > ../logs/frontend_startup.log 2>&1 & cd ..

echo "🔍 Waiting for servers to start..."
sleep 10

# Quick health check
if curl -s --max-time 3 http://localhost:8000/health > /dev/null; then
    echo "✅ Backend: Ready"
else
    echo "⚠️  Backend: Starting..."
fi

if curl -s --max-time 3 http://localhost:3000 > /dev/null; then
    echo "✅ Frontend: Ready"
else
    echo "⚠️  Frontend: Starting..."
fi

echo ""
echo "🎉 Quick restart completed!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"