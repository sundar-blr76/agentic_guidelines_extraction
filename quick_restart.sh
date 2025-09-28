#!/bin/bash
# Quick restart - simplified version for daily use

echo "🔄 Quick Server Restart..."

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