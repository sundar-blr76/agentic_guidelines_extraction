#!/bin/bash

# Comprehensive API Testing Script
# Tests all endpoints and provides detailed feedback

echo "🧪 Starting Comprehensive API Testing..."

BASE_URL="http://localhost:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
print_test_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $test_name: $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC} - $test_name: $message"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo -e "${YELLOW}⚠️  WARN${NC} - $test_name: $message"
    fi
}

# Function to test endpoint
test_endpoint() {
    local endpoint="$1"
    local expected_status="$2"
    local test_name="$3"
    local method="${4:-GET}"
    
    echo -e "${BLUE}🔍 Testing: ${NC}$test_name"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$BASE_URL$endpoint")
    fi
    
    http_status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo "$response" | sed -e 's/HTTPSTATUS:.*//g')
    
    if [ "$http_status" = "$expected_status" ]; then
        print_test_result "$test_name" "PASS" "Status: $http_status"
        if [ ! -z "$body" ] && [ "$body" != "" ]; then
            echo "   📄 Response: $body" | head -c 200
            [ ${#body} -gt 200 ] && echo "..."
            echo ""
        fi
    else
        print_test_result "$test_name" "FAIL" "Expected: $expected_status, Got: $http_status"
        echo "   📄 Response: $body"
    fi
    
    echo ""
}

# Function to test sessions endpoint
test_sessions() {
    echo -e "${BLUE}🔍 Testing: ${NC}Sessions Management"
    
    # Get sessions
    response=$(curl -s "$BASE_URL/sessions")
    if echo "$response" | grep -q '"success":true'; then
        print_test_result "Get Sessions" "PASS" "Successfully retrieved sessions"
    else
        print_test_result "Get Sessions" "FAIL" "Failed to retrieve sessions"
    fi
    
    # Create session
    response=$(curl -s -X POST "$BASE_URL/sessions" \
        -H "Content-Type: application/json" \
        -d '{"user_id": "test_user"}')
    if echo "$response" | grep -q '"session_id"'; then
        session_id=$(echo "$response" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
        print_test_result "Create Session" "PASS" "Created session: $session_id"
        
        # Test chat with new session
        chat_response=$(curl -s -X POST "$BASE_URL/agent/chat" \
            -H "Content-Type: application/json" \
            -d "{\"message\":\"Hello test\",\"session_id\":\"$session_id\"}")
        
        if echo "$chat_response" | grep -q '"response"'; then
            print_test_result "Chat Test" "PASS" "Chat response received"
        else
            print_test_result "Chat Test" "FAIL" "No chat response"
        fi
    else
        print_test_result "Create Session" "FAIL" "Failed to create session"
    fi
    
    echo ""
}

# Function to test file upload simulation
test_file_upload() {
    echo -e "${BLUE}🔍 Testing: ${NC}File Upload Simulation"
    
    # Check if sample file exists
    sample_file="sample_docs/PRIM-Investment-Policy-Statement-02152024.pdf"
    if [ -f "$sample_file" ]; then
        echo "   📁 Using sample file: $sample_file"
        
        # Test file upload
        response=$(curl -s -X POST "$BASE_URL/agent/ingest" \
            -F "file=@$sample_file")
        
        if echo "$response" | grep -q '"success":true'; then
            print_test_result "Document Ingestion" "PASS" "Document ingested successfully"
            
            # Extract details from response
            if echo "$response" | grep -q '"doc_id"'; then
                doc_id=$(echo "$response" | grep -o '"doc_id":"[^"]*"' | cut -d'"' -f4)
                echo "   📄 Document ID: $doc_id"
            fi
            
            if echo "$response" | grep -q '"guidelines_count"'; then
                guidelines_count=$(echo "$response" | grep -o '"guidelines_count":[0-9]*' | cut -d':' -f2)
                echo "   📊 Guidelines count: $guidelines_count"
            fi
            
        elif echo "$response" | grep -q '"success":false'; then
            error_msg=$(echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
            if echo "$error_msg" | grep -q "Service Unavailable\|503\|rate limit"; then
                print_test_result "Document Ingestion" "WARN" "LLM service temporarily unavailable: $error_msg"
            else
                print_test_result "Document Ingestion" "FAIL" "Error: $error_msg"
            fi
        else
            print_test_result "Document Ingestion" "FAIL" "Unexpected response format"
        fi
    else
        print_test_result "Document Ingestion" "WARN" "No sample file found at $sample_file"
    fi
    
    echo ""
}

# Main testing sequence
echo "🚀 Starting endpoint tests..."
echo "=================================================="

# Basic health and info endpoints
test_endpoint "/health" "200" "Health Check"
test_endpoint "/" "200" "Root Endpoint"

# Sessions management
test_sessions

# Agent endpoints
test_endpoint "/agent/stats" "200" "Agent Statistics"

# File upload test
test_file_upload

# Guidelines endpoints
response=$(curl -s -X POST "$BASE_URL/mcp/query_guidelines" \
    -H "Content-Type: application/json" \
    -d '{"query_text": "test", "top_k": 5}')
if echo "$response" | grep -q '"success":true'; then
    print_test_result "Guidelines Search" "PASS" "Guidelines search completed"
else
    print_test_result "Guidelines Search" "FAIL" "Guidelines search failed"
fi

# Print final results
echo "=================================================="
echo -e "${BLUE}📊 TEST SUMMARY${NC}"
echo "=================================================="
echo -e "Tests Run:    ${TESTS_RUN}"
echo -e "Passed:       ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Failed:       ${RED}${TESTS_FAILED}${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  SOME TESTS FAILED${NC}"
    exit 1
fi