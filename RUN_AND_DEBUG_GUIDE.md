# 🚀 Guidelines Agent - Run and Debug Guide

## Overview

This comprehensive guide covers everything you need to run, manage, and debug the Guidelines Agent application. The project uses 9 optimized scripts for development, server management, and testing.

---

## 🎯 Quick Start

### For New Developers
```bash
# 1. Check what's available
./show_usage.sh

# 2. Start everything with verification
./restart_servers.sh

# 3. Test that it works
./test_quick.sh

# 4. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### For Daily Development
```bash
# Fast restart during active development
./quick_restart.sh

# Backend changes only
./restart_servers.sh --backend-only

# Before committing changes
./test_quick.sh
```

---

## 🔧 Server Management Scripts

### 1. `./restart_servers.sh` - Master Server Management
**Primary script for comprehensive server operations**

```bash
# Full restart with health verification (most common)
./restart_servers.sh

# Backend development (API changes)
./restart_servers.sh --backend-only

# Frontend development (UI changes)  
./restart_servers.sh --frontend-only

# Check server status and running processes
./restart_servers.sh --status

# View recent log files for debugging
./restart_servers.sh --logs

# Clean shutdown of all servers
./restart_servers.sh --kill-only

# Show detailed help
./restart_servers.sh --help
```

**Features:**
- ✅ Kills existing processes on ports 8000 and 3000
- ✅ Clears all log files (configurable)
- ✅ Starts servers with proper virtual environment
- ✅ Waits for servers to be ready (health checks)
- ✅ Verifies API endpoints are working
- ✅ Shows process status and diagnostics
- ✅ Provides colored output for easy reading

### 2. `./quick_restart.sh` - Fast Development Restarts
**Lightweight script for frequent daily restarts**

```bash
# Fast restart both servers (most common during development)
./quick_restart.sh
```

**Features:**
- ⚡ Fast execution (no health checks or extended waiting)
- 🧹 Clears main API log file
- 🔄 Starts both servers in background
- 💨 Optimized for speed over verification

### 3. Individual Server Scripts
```bash
# Backend only
./start_server.sh

# Frontend only
./start_frontend.sh
```

---

## 🧪 Testing and Verification

### Quick Testing
```bash
# Fast regression test
./test_quick.sh

# Comprehensive API testing
./test_comprehensive_api.sh

# Full test suite with server management
./comprehensive_test.sh
```

### Test Options
```bash
# Health checks only
./comprehensive_test.sh --health-only

# API tests only
./comprehensive_test.sh --api-only

# System status only
./comprehensive_test.sh --status-only
```

---

## 🌐 Application URLs and Access

### Frontend
- **Main UI:** http://localhost:3000
- **Development server with hot-reload**

### Backend
- **API Server:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### Key Features
- **Document Ingestion:** Upload PDFs to extract investment guidelines
- **AI Query Interface:** Ask questions about investment policies
- **Session Management:** Persistent conversations
- **Real-time Processing:** Live feedback during operations

---

## 📋 Log Files and Monitoring

### Log Locations
```bash
logs/api_server.log         # Main API server log with IST timestamps
logs/backend_startup.log    # Backend startup messages
logs/frontend_startup.log   # Frontend startup messages
logs/backend.pid           # Backend process ID
logs/frontend.pid          # Frontend process ID
```

### Monitoring Commands
```bash
# View logs in real-time
tail -f logs/api_server.log

# Check recent logs
./restart_servers.sh --logs

# Check server status
./restart_servers.sh --status

# View process information
ps aux | grep -E "(python|node)"
```

---

## 🛠️ Development Workflows

### Morning Startup
```bash
# Start with full verification (recommended)
./restart_servers.sh

# Or if servers are already running
./restart_servers.sh --status
```

### Active Development
```bash
# Fast restarts during coding
./quick_restart.sh

# Backend changes only (faster)
./restart_servers.sh --backend-only

# Frontend changes only
./restart_servers.sh --frontend-only
```

### Before Committing
```bash
# Quick regression test
./test_quick.sh

# Full verification if needed
./comprehensive_test.sh
```

### End of Day
```bash
# Clean shutdown
./restart_servers.sh --kill-only
```

---

## 🐛 Troubleshooting Guide

### Server Won't Start

**Check ports and processes:**
```bash
./restart_servers.sh --status
lsof -i:8000 && lsof -i:3000
```

**Force clean restart:**
```bash
./restart_servers.sh --kill-only
./restart_servers.sh
```

**Check logs for errors:**
```bash
./restart_servers.sh --logs
tail -f logs/api_server.log
```

### API Not Responding

**Restart backend only:**
```bash
./restart_servers.sh --backend-only
```

**Test health endpoint:**
```bash
curl http://localhost:8000/health
```

**Check API logs:**
```bash
grep ERROR logs/api_server.log
```

### Frontend Not Loading

**Restart frontend only:**
```bash
./restart_servers.sh --frontend-only
```

**Check dependencies:**
```bash
cd frontend && npm install
```

**Verify React server:**
```bash
curl http://localhost:3000
```

### Document Ingestion Issues

**Check LLM API logs:**
```bash
grep -A5 -B5 "LLM REQUEST\|FAILED LLM\|SUCCESS LLM" logs/api_server.log
```

**Common issues:**
- **Rate limits:** Wait and retry
- **Large files:** Check file size limits
- **API keys:** Verify environment variables
- **Network:** Check internet connectivity

### Database Issues

**Check for duplicate inserts:**
```bash
grep "portfolio_name.*already exists" logs/api_server.log
```

**Verify database connections:**
```bash
grep -i "database\|connection" logs/api_server.log
```

---

## ⚡ Performance Optimization

### Caching System
```bash
# Use centralized caching
./run-with-cache.sh python -m pytest
./run-with-cache.sh python script.py
```

**Cache directories:**
- `.build_cache/pycache/` - Python cache
- `.build_cache/pytest/` - Pytest cache  
- `.build_cache/ruff/` - Ruff linter cache

### Development Tips
- Keep `./quick_restart.sh` for frequent changes
- Use `./restart_servers.sh` when you need verification
- Monitor logs in separate terminal: `tail -f logs/api_server.log`
- Run backend-only when working on API changes

---

## 🔍 Debug Information

### System Status Check
```bash
./restart_servers.sh --status
```
**Shows:**
- Running processes and PIDs
- Port usage
- Log file sizes
- Server response status

### Health Verification
```bash
curl -s http://localhost:8000/health | jq
curl -s http://localhost:3000  # Should return HTML
```

### Process Management
```bash
# List all related processes
ps aux | grep -E "(uvicorn|node|python.*guidelines)"

# Check port usage
netstat -tulnp | grep -E ":3000|:8000"

# Memory usage
ps -o pid,ppid,cmd,%mem,%cpu -p $(cat logs/backend.pid logs/frontend.pid 2>/dev/null)
```

---

## 📞 Getting Help

### Built-in Help
```bash
./show_usage.sh                 # Comprehensive usage guide
./restart_servers.sh --help     # Server management help
./comprehensive_test.sh --help  # Testing help
```

### Quick Reference
- **Status check:** `./restart_servers.sh --status`
- **View logs:** `./restart_servers.sh --logs`
- **Fast restart:** `./quick_restart.sh`
- **Full restart:** `./restart_servers.sh`
- **Test quickly:** `./test_quick.sh`

### Common Commands
```bash
# Check if everything is working
./restart_servers.sh && ./test_quick.sh

# Debug startup issues
./restart_servers.sh --kill-only && ./restart_servers.sh --logs

# Full system verification
./comprehensive_test.sh
```

---

## 🎯 Best Practices

1. **Always use `./restart_servers.sh` for important changes**
2. **Use `./quick_restart.sh` for frequent development cycles**  
3. **Check `--status` when something seems wrong**
4. **Monitor logs during debugging: `tail -f logs/api_server.log`**
5. **Run `./test_quick.sh` before committing**
6. **Use `--backend-only` for API-only changes**
7. **Keep the comprehensive test passing at 85%+**

This guide should cover all your development and debugging needs for the Guidelines Agent application.