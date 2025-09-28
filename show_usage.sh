#!/bin/bash
# Display script usage and examples - can be called directly or from other scripts

cat << 'EOF'
🚀 Guidelines Agent - Server Management Scripts
==============================================

📋 AVAILABLE SCRIPTS:

1️⃣  ./restart_servers.sh     - Comprehensive server management
2️⃣  ./quick_restart.sh       - Fast daily development restarts  
3️⃣  ./start_server.sh        - Backend server only
4️⃣  ./test_quick.sh          - Run regression tests

🎯 COMMON USAGE PATTERNS:

# 🔄 DAILY DEVELOPMENT
./quick_restart.sh                    # Fast restart during active development
./restart_servers.sh --backend-only   # Backend changes only
./restart_servers.sh --frontend-only  # Frontend/UI changes only

# 🧪 AFTER MAJOR CHANGES  
./restart_servers.sh                  # Full restart with health verification
./test_quick.sh                       # Run regression tests
./restart_servers.sh --status         # Verify everything is working

# 🐛 DEBUGGING ISSUES
./restart_servers.sh --logs           # Check recent log files
./restart_servers.sh --status         # See what processes are running
./restart_servers.sh --kill-only      # Clean shutdown all servers

# 🚦 STATUS MONITORING
./restart_servers.sh --status         # Current server status
curl http://localhost:8000/health     # Backend health check
curl http://localhost:3000             # Frontend accessibility

🌐 SERVER URLS:
┌─────────────────────────────────────────────┐
│ 🎨 Frontend UI:    http://localhost:3000   │
│ 🔧 Backend API:    http://localhost:8000   │  
│ 📚 API Docs:       http://localhost:8000/docs │
│ 💓 Health Check:   http://localhost:8000/health │
└─────────────────────────────────────────────┘

📋 LOG FILES:
• logs/api_server.log         - Main API server log (cleared on restart)
• logs/backend_startup.log    - Backend startup messages
• logs/frontend_startup.log   - Frontend startup messages  
• logs/backend.pid           - Backend process ID
• logs/frontend.pid          - Frontend process ID

🛠️  TROUBLESHOOTING GUIDE:

❓ Servers won't start?
   ./restart_servers.sh --kill-only    # Force stop all processes
   ./restart_servers.sh --logs         # Check error messages
   lsof -i:8000 && lsof -i:3000       # Check port usage

❓ API not responding?
   ./restart_servers.sh --backend-only # Restart just backend
   curl http://localhost:8000/health   # Test health endpoint
   ./restart_servers.sh --status       # Check process status

❓ Frontend not loading?
   ./restart_servers.sh --frontend-only # Restart just frontend  
   cd frontend && npm install          # Reinstall dependencies
   ./restart_servers.sh --logs         # Check startup errors

❓ Tests failing?
   ./restart_servers.sh                # Ensure servers are healthy
   ./test_quick.sh                     # Run regression tests
   ./tests/run_tests.sh --unit-only    # Run just unit tests

🏆 RECOMMENDED DEVELOPMENT WORKFLOW:

Morning startup:        ./restart_servers.sh
During development:     ./quick_restart.sh  
After code changes:     ./restart_servers.sh --backend-only
Before committing:      ./test_quick.sh
End of day cleanup:     ./restart_servers.sh --kill-only

💡 PRO TIPS:
• Use quick_restart.sh for frequent restarts (faster)
• Use restart_servers.sh when you need verification
• Always check --status if something seems wrong
• Keep frontend and backend logs separate for easier debugging
• Use --logs option to quickly diagnose startup issues

📞 NEED HELP?
Run any script with --help for detailed usage information.

EOF