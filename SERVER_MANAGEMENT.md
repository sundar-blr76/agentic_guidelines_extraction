# Server Management Scripts

This directory contains several scripts for managing the Guidelines Agent servers:

## 🚀 Main Scripts

### `restart_servers.sh` - Comprehensive Server Management
The primary script for managing both frontend and backend servers.

**Features:**
- ✅ Kills existing processes on ports 8000 and 3000
- ✅ Clears all log files automatically
- ✅ Starts servers with proper health checks
- ✅ Waits for servers to be ready before completing
- ✅ Verifies API endpoints are working
- ✅ Shows process status and diagnostics

**Usage:**
```bash
# Restart both servers (default)
./restart_servers.sh

# Backend only
./restart_servers.sh --backend-only

# Frontend only  
./restart_servers.sh --frontend-only

# Kill all servers without restarting
./restart_servers.sh --kill-only

# Check server status
./restart_servers.sh --status

# View recent logs
./restart_servers.sh --logs

# Show help
./restart_servers.sh --help
```

### `quick_restart.sh` - Fast Restart
Simple script for quick daily restarts during development.

**Features:**
- ⚡ Fast execution (no waiting/verification)
- 🧹 Clears main log file
- 🔄 Restarts both servers in background

**Usage:**
```bash
./quick_restart.sh
```

### `start_server.sh` - Backend Only
Original script for starting just the backend server.

**Usage:**
```bash
./start_server.sh
```

## 📊 Server Information

**Backend Server:**
- URL: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**Frontend Server:**
- URL: http://localhost:3000
- Development server with hot reload

## 📋 Log Files

**Main Logs:**
- `logs/api_server.log` - Main API server log with IST timestamps
- `logs/backend_startup.log` - Backend startup messages
- `logs/frontend_startup.log` - Frontend startup messages

**Process Tracking:**
- `logs/backend.pid` - Backend process ID
- `logs/frontend.pid` - Frontend process ID

## 🔧 Troubleshooting

**If servers won't start:**
1. Use `./restart_servers.sh --kill-only` to force stop all processes
2. Check logs: `./restart_servers.sh --logs`
3. Verify ports are free: `lsof -i:8000` and `lsof -i:3000`
4. Try backend only first: `./restart_servers.sh --backend-only`

**Common Issues:**
- **Port conflicts**: Script automatically kills existing processes
- **Virtual environment**: Script automatically activates venv if present
- **Dependencies**: Frontend script will run `npm install` if node_modules missing
- **Permissions**: All scripts are executable

## 🎯 Recommended Workflow

**Daily development:**
```bash
./quick_restart.sh     # Fast restart for quick changes
```

**After code changes:**
```bash
./restart_servers.sh   # Full restart with verification
```

**Debugging issues:**
```bash
./restart_servers.sh --status  # Check what's running
./restart_servers.sh --logs    # View recent logs
```

**Clean shutdown:**
```bash
./restart_servers.sh --kill-only  # Stop all servers
```

All scripts include proper error handling, colored output, and comprehensive logging for easy troubleshooting.