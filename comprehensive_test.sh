#!/bin/bash

# comprehensive_test.sh - Script to test all API endpoints comprehensively

set -e  # Exit on any error

echo "🚀 Guidelines Agent Comprehensive Testing Suite"
echo "=============================================="

# Configuration
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
LOG_DIR="logs"
TEST_RESULTS_FILE="test_results_$(date +%Y%m%d_%H%M%S).txt"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Function to check if server is running
check_server() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Checking $name server at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
            print_success "$name server is running"
            return 0
        fi
        
        if [ $attempt -eq 1 ]; then
            print_status "Waiting for $name server to start..."
        fi
        
        sleep 2
        ((attempt++))
    done
    
    print_error "$name server is not responding after ${max_attempts} attempts"
    return 1
}

# Function to run API tests
run_api_tests() {
    print_status "Running comprehensive API tests..."
    
    # Check if Python environment is activated
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found"
        return 1
    fi
    
    # Install required packages if not present
    if ! python3 -c "import requests" &> /dev/null; then
        print_status "Installing requests package..."
        pip install requests
    fi
    
    if ! python3 -c "import pytest" &> /dev/null; then
        print_status "Installing pytest package..."
        pip install pytest
    fi
    
    # Run the comprehensive tests
    print_status "Executing comprehensive test suite..."
    if python3 tests/test_endpoints_comprehensive.py 2>&1 | tee "$TEST_RESULTS_FILE"; then
        print_success "API tests completed - see $TEST_RESULTS_FILE for details"
        return 0
    else
        print_error "API tests failed - see $TEST_RESULTS_FILE for details"
        return 1
    fi
}

# Function to run quick health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Check API server health
    if response=$(curl -s "$API_URL/health" 2>/dev/null); then
        print_success "API Health: $response"
    else
        print_error "API health check failed"
        return 1
    fi
    
    # Check frontend
    if curl -s -o /dev/null "$FRONTEND_URL" 2>/dev/null; then
        print_success "Frontend is accessible"
    else
        print_warning "Frontend may not be running or accessible"
    fi
    
    # Check API endpoints availability
    endpoints=(
        "/health"
        "/sessions"
        "/agent/stats"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s -o /dev/null "$API_URL$endpoint" 2>/dev/null; then
            print_success "Endpoint $endpoint is accessible"
        else
            print_error "Endpoint $endpoint is not accessible"
        fi
    done
}

# Function to show system status
show_system_status() {
    print_status "System Status Overview"
    echo "======================"
    
    # Check running processes
    print_status "Checking running processes..."
    if pgrep -f "uvicorn.*guidelines_agent" > /dev/null; then
        print_success "API server (uvicorn) is running"
        ps aux | grep -E "uvicorn.*guidelines_agent" | grep -v grep
    else
        print_warning "API server may not be running"
    fi
    
    if pgrep -f "npm.*start" > /dev/null || pgrep -f "react-scripts" > /dev/null; then
        print_success "Frontend server is running" 
        ps aux | grep -E "npm.*start|react-scripts" | grep -v grep | head -2
    else
        print_warning "Frontend server may not be running"
    fi
    
    # Show log file info
    print_status "Log files status:"
    if [ -f "$LOG_DIR/api_server.log" ]; then
        log_lines=$(wc -l < "$LOG_DIR/api_server.log")
        log_size=$(du -h "$LOG_DIR/api_server.log" | cut -f1)
        print_success "API log: $log_lines lines, $log_size"
    else
        print_warning "No API log file found"
    fi
    
    # Show available endpoints
    print_status "Testing core endpoints..."
    
    if curl -s "$API_URL/docs" > /dev/null 2>&1; then
        print_success "API documentation available at $API_URL/docs"
    fi
}

# Function to generate test report
generate_report() {
    local test_file=$1
    if [ ! -f "$test_file" ]; then
        print_warning "No test results file found"
        return
    fi
    
    print_status "Test Report Summary"
    echo "==================="
    
    # Extract key metrics from test results
    if grep -q "Success Rate:" "$test_file"; then
        success_rate=$(grep "Success Rate:" "$test_file" | tail -1)
        print_success "$success_rate"
    fi
    
    if grep -q "Passed:" "$test_file"; then
        passed=$(grep "Passed:" "$test_file" | tail -1)
        print_success "$passed"
    fi
    
    if grep -q "Failed:" "$test_file"; then
        failed=$(grep "Failed:" "$test_file" | tail -1)
        if echo "$failed" | grep -q "Failed: 0"; then
            print_success "$failed"
        else
            print_error "$failed"
        fi
    fi
    
    # Show any errors
    if grep -q "❌ FAILED" "$test_file"; then
        print_status "Failed tests:"
        grep "❌ FAILED" "$test_file" || true
    fi
}

# Main execution
main() {
    print_status "Starting comprehensive testing suite..."
    
    # Create logs directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Show system status first
    show_system_status
    
    # Check if servers are running
    if ! check_server "$API_URL/health" "API"; then
        print_error "API server is required for testing. Please start with:"
        echo "  python3 -m uvicorn guidelines_agent.main:app --host 0.0.0.0 --port 8000 --reload"
        exit 1
    fi
    
    check_server "$FRONTEND_URL" "Frontend" || print_warning "Frontend not running - some integration tests may be skipped"
    
    # Run health checks
    print_status "\n🔍 Running health checks..."
    run_health_checks || print_warning "Some health checks failed"
    
    # Run comprehensive API tests
    print_status "\n🧪 Running comprehensive API tests..."
    if run_api_tests; then
        print_success "All API tests completed successfully"
    else
        print_error "Some API tests failed"
    fi
    
    # Generate report
    print_status "\n📊 Generating test report..."
    generate_report "$TEST_RESULTS_FILE"
    
    print_status "\n✨ Testing completed!"
    print_status "Full results saved to: $TEST_RESULTS_FILE"
    print_status "API Documentation: $API_URL/docs"
    print_status "Frontend: $FRONTEND_URL"
}

# Help function
show_help() {
    echo "Guidelines Agent Comprehensive Test Suite"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --health-only    Run only health checks"
    echo "  --api-only       Run only API tests"
    echo "  --status-only    Show only system status"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run full test suite"
    echo "  $0 --health-only     # Quick health check"
    echo "  $0 --api-only        # API tests only"
}

# Parse command line arguments
case "${1:-}" in
    --health-only)
        show_system_status
        run_health_checks
        ;;
    --api-only)
        check_server "$API_URL/health" "API" || exit 1
        run_api_tests
        ;;
    --status-only)
        show_system_status
        ;;
    --help)
        show_help
        ;;
    *)
        main "$@"
        ;;
esac