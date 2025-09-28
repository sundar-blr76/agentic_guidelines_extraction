#!/bin/bash
# Comprehensive test runner script

set -e

echo "🧪 Guidelines Agent API Test Suite"
echo "=================================="

# Configuration
BASE_URL="http://localhost:8000"
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$TEST_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_server() {
    log_info "Checking server availability at $BASE_URL..."
    
    if curl -s --max-time 5 "$BASE_URL/health" > /dev/null; then
        log_info "Server is accessible"
        return 0
    else
        log_error "Server not accessible at $BASE_URL"
        log_warn "Please start the server with: ./start_server.sh"
        return 1
    fi
}

run_unit_tests() {
    log_info "Running unit tests..."
    
    cd "$PROJECT_ROOT"
    
    if command -v pytest &> /dev/null; then
        python3 -m pytest tests/unit/ -v --tb=short
        return $?
    else
        log_warn "pytest not found, running with python3 -m unittest"
        python3 -m unittest discover tests/unit/ -v
        return $?
    fi
}

run_integration_tests() {
    log_info "Running integration tests..."
    
    cd "$TEST_DIR/integration"
    python3 test_api_regression.py
    return $?
}

run_performance_tests() {
    log_info "Running performance tests..."
    
    cd "$PROJECT_ROOT"
    
    if command -v pytest &> /dev/null; then
        python3 -m pytest tests/unit/test_components.py::TestPerformance -v -m performance
        return $?
    else
        log_warn "Skipping performance tests (requires pytest)"
        return 0
    fi
}

generate_coverage_report() {
    log_info "Generating test coverage report..."
    
    cd "$PROJECT_ROOT"
    
    if command -v pytest &> /dev/null && python3 -c "import pytest_cov" 2>/dev/null; then
        python3 -m pytest tests/ --cov=guidelines_agent --cov-report=html --cov-report=term
        log_info "Coverage report generated in htmlcov/"
        return $?
    else
        log_warn "Coverage reporting not available (requires pytest-cov)"
        return 0
    fi
}

main() {
    local run_unit=true
    local run_integration=true
    local run_performance=false
    local generate_coverage=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit-only)
                run_integration=false
                shift
                ;;
            --integration-only)
                run_unit=false
                shift
                ;;
            --performance)
                run_performance=true
                shift
                ;;
            --coverage)
                generate_coverage=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --unit-only      Run only unit tests"
                echo "  --integration-only Run only integration tests"
                echo "  --performance    Include performance tests"
                echo "  --coverage       Generate coverage report"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    log_info "Starting test suite..."
    log_info "Project root: $PROJECT_ROOT"
    log_info "Test directory: $TEST_DIR"
    
    local exit_code=0
    
    # Check dependencies
    if ! python3 -c "import requests" 2>/dev/null; then
        log_error "Missing required dependency: requests"
        log_info "Install with: pip install requests"
        exit 1
    fi
    
    # Run unit tests
    if [[ "$run_unit" == true ]]; then
        echo ""
        if run_unit_tests; then
            log_info "Unit tests passed ✅"
        else
            log_error "Unit tests failed ❌"
            exit_code=1
        fi
    fi
    
    # Check server for integration tests
    if [[ "$run_integration" == true ]]; then
        echo ""
        if ! check_server; then
            log_error "Cannot run integration tests without server"
            exit_code=1
        else
            if run_integration_tests; then
                log_info "Integration tests passed ✅"
            else
                log_error "Integration tests failed ❌"
                exit_code=1
            fi
        fi
    fi
    
    # Run performance tests
    if [[ "$run_performance" == true ]]; then
        echo ""
        if check_server; then
            if run_performance_tests; then
                log_info "Performance tests passed ✅"
            else
                log_error "Performance tests failed ❌"
                exit_code=1
            fi
        else
            log_warn "Skipping performance tests (server not available)"
        fi
    fi
    
    # Generate coverage report
    if [[ "$generate_coverage" == true ]]; then
        echo ""
        generate_coverage_report
    fi
    
    # Final summary
    echo ""
    echo "=================================="
    if [[ $exit_code -eq 0 ]]; then
        log_info "All tests completed successfully! 🎉"
    else
        log_error "Some tests failed. Check output above for details."
    fi
    echo "=================================="
    
    return $exit_code
}

# Run main function with all arguments
main "$@"