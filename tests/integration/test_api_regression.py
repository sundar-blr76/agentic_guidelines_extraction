"""
Comprehensive regression test suite for Guidelines Agent API.

Tests all endpoints with various scenarios:
- Health checks
- Agent interactions (chat, query, ingest)
- Session management
- MCP internal tools
- Error handling
- Authentication (future)
"""
import pytest
import requests
import json
import time
import tempfile
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

@dataclass
class TestResult:
    """Test result data structure."""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    success: bool
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class GuidelinesAgentTester:
    """Main test class for Guidelines Agent API."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.session_ids = []  # Track created sessions for cleanup
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> TestResult:
        """Make HTTP request and return structured result."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.session.request(method, url, timeout=TIMEOUT, **kwargs)
            response_time = time.time() - start_time
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            result = TestResult(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time=response_time,
                success=200 <= response.status_code < 300,
                response_data=response_data
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time=response_time,
                success=False,
                error_message=str(e)
            )
        
        self.test_results.append(result)
        return result
    
    # =====================================
    # HEALTH AND INFO ENDPOINTS
    # =====================================
    
    def test_health_endpoint(self) -> TestResult:
        """Test /health endpoint."""
        print("🏥 Testing health endpoint...")
        result = self._make_request("GET", "/health")
        
        if result.success:
            assert result.response_data.get("success") is True
            assert "healthy" in result.response_data.get("status", "").lower()
            print(f"  ✅ Health check passed ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ Health check failed: {result.error_message}")
        
        return result
    
    def test_root_endpoint(self) -> TestResult:
        """Test root / endpoint."""
        print("🏠 Testing root endpoint...")
        result = self._make_request("GET", "/")
        
        if result.success:
            assert result.response_data.get("success") is True
            assert "Guidelines Agent API" in result.response_data.get("message", "")
            print(f"  ✅ Root endpoint passed ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ Root endpoint failed: {result.error_message}")
        
        return result
    
    # =====================================
    # AGENT ENDPOINTS
    # =====================================
    
    def test_agent_stats(self) -> TestResult:
        """Test GET /agent/stats endpoint."""
        print("📊 Testing agent stats...")
        result = self._make_request("GET", "/agent/stats")
        
        if result.success:
            stats = result.response_data.get("stats", {})
            assert "total_portfolios" in stats
            assert "total_guidelines" in stats
            print(f"  ✅ Found {stats.get('total_portfolios', 0)} portfolios, {stats.get('total_guidelines', 0)} guidelines ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ Agent stats failed: {result.error_message}")
        
        return result
    
    def test_agent_query(self) -> TestResult:
        """Test POST /agent/query endpoint."""
        print("🔍 Testing agent query...")
        
        payload = {
            "query": "What are the investment restrictions?",
            "portfolio_ids": None
        }
        
        result = self._make_request("POST", "/agent/query", 
                                  json=payload, 
                                  headers={"Content-Type": "application/json"})
        
        if result.success:
            assert result.response_data.get("success") is True
            assert "response" in result.response_data
            print(f"  ✅ Query processed successfully ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ Agent query failed: {result.error_message}")
        
        return result
    
    def test_agent_chat(self) -> TestResult:
        """Test POST /agent/chat endpoint."""
        print("💬 Testing agent chat...")
        
        payload = {
            "message": "Hello! Can you help me understand investment guidelines?"
        }
        
        result = self._make_request("POST", "/agent/chat",
                                  json=payload,
                                  headers={"Content-Type": "application/json"})
        
        if result.success:
            assert result.response_data.get("success") is True
            assert "response" in result.response_data
            assert "session_id" in result.response_data
            
            # Track session for cleanup
            session_id = result.response_data.get("session_id")
            if session_id:
                self.session_ids.append(session_id)
            
            print(f"  ✅ Chat successful, session: {session_id[:8]}... ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ Agent chat failed: {result.error_message}")
        
        return result
    
    def test_agent_chat_with_session(self) -> TestResult:
        """Test POST /agent/chat with existing session."""
        print("💬 Testing agent chat with session continuity...")
        
        # First message
        payload1 = {
            "message": "What is rebalancing?"
        }
        
        result1 = self._make_request("POST", "/agent/chat",
                                   json=payload1,
                                   headers={"Content-Type": "application/json"})
        
        if not result1.success:
            print(f"  ❌ First chat failed: {result1.error_message}")
            return result1
        
        session_id = result1.response_data.get("session_id")
        self.session_ids.append(session_id)
        
        # Follow-up message using same session
        payload2 = {
            "message": "Can you give me more details about what we just discussed?",
            "session_id": session_id
        }
        
        result2 = self._make_request("POST", "/agent/chat",
                                   json=payload2,
                                   headers={"Content-Type": "application/json"})
        
        if result2.success:
            assert result2.response_data.get("session_id") == session_id
            print(f"  ✅ Session continuity working ({result2.response_time:.2f}s)")
        else:
            print(f"  ❌ Session continuity failed: {result2.error_message}")
        
        return result2
    
    # =====================================
    # SESSION ENDPOINTS
    # =====================================
    
    def test_session_create(self) -> TestResult:
        """Test POST /sessions endpoint."""
        print("🆕 Testing session creation...")
        
        payload = {"user_id": "test_user"}
        
        result = self._make_request("POST", "/sessions",
                                  json=payload,
                                  headers={"Content-Type": "application/json"})
        
        if result.success:
            assert result.response_data.get("success") is True
            assert "session_id" in result.response_data
            
            session_id = result.response_data.get("session_id")
            self.session_ids.append(session_id)
            print(f"  ✅ Session created: {session_id[:8]}... ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ Session creation failed: {result.error_message}")
        
        return result
    
    def test_session_info(self) -> TestResult:
        """Test GET /sessions/{session_id} endpoint."""
        print("ℹ️ Testing session info...")
        
        # Create a session first
        create_result = self.test_session_create()
        if not create_result.success:
            return create_result
        
        session_id = create_result.response_data.get("session_id")
        
        # Get session info
        result = self._make_request("GET", f"/sessions/{session_id}")
        
        if result.success:
            assert result.response_data.get("success") is True
            session_data = result.response_data.get("session", {})
            assert session_data.get("session_id") == session_id
            print(f"  ✅ Session info retrieved ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ Session info failed: {result.error_message}")
        
        return result
    
    def test_session_stats(self) -> TestResult:
        """Test GET /sessions endpoint for stats."""
        print("📈 Testing session stats...")
        
        result = self._make_request("GET", "/sessions")
        
        if result.success:
            stats = result.response_data.get("stats", {})
            assert "total_sessions" in stats
            print(f"  ✅ Session stats: {stats.get('total_sessions', 0)} total sessions ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ Session stats failed: {result.error_message}")
        
        return result
    
    # =====================================
    # MCP INTERNAL ENDPOINTS  
    # =====================================
    
    def test_mcp_plan_query(self) -> TestResult:
        """Test POST /mcp/plan_query endpoint."""
        print("🎯 Testing MCP query planning...")
        
        payload = {
            "user_query": "What are the risk management guidelines?"
        }
        
        result = self._make_request("POST", "/mcp/plan_query",
                                  json=payload,
                                  headers={"Content-Type": "application/json"})
        
        if result.success:
            assert "search_query" in result.response_data
            assert "summary_instruction" in result.response_data
            assert "top_k" in result.response_data
            print(f"  ✅ Query planning successful ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ MCP query planning failed: {result.error_message}")
        
        return result
    
    def test_mcp_query_guidelines(self) -> TestResult:
        """Test POST /mcp/query_guidelines endpoint."""
        print("🔍 Testing MCP guideline search...")
        
        payload = {
            "query_text": "investment restrictions equity",
            "top_k": 5
        }
        
        result = self._make_request("POST", "/mcp/query_guidelines",
                                  json=payload,
                                  headers={"Content-Type": "application/json"})
        
        if result.success:
            assert result.response_data.get("success") is True
            data = result.response_data.get("data", {})
            results = data.get("results", [])
            print(f"  ✅ Found {len(results)} guidelines ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ MCP guideline search failed: {result.error_message}")
        
        return result
    
    def test_mcp_summarize(self) -> TestResult:
        """Test POST /mcp/summarize endpoint."""
        print("📝 Testing MCP summarization...")
        
        payload = {
            "question": "What are the investment restrictions?",
            "sources": [
                "The fund shall not invest more than 5% in any single security.",
                "Investments in derivatives are limited to hedging purposes only.",
                "Alternative investments are capped at 15% of total portfolio."
            ]
        }
        
        result = self._make_request("POST", "/mcp/summarize",
                                  json=payload,
                                  headers={"Content-Type": "application/json"})
        
        if result.success:
            assert result.response_data.get("success") is True
            summary = result.response_data.get("data", {}).get("summary", "")
            assert len(summary) > 50  # Should have substantial content
            print(f"  ✅ Summarization successful ({result.response_time:.2f}s)")
        else:
            print(f"  ❌ MCP summarization failed: {result.error_message}")
        
        return result
    
    # =====================================
    # ERROR HANDLING TESTS
    # =====================================
    
    def test_invalid_endpoints(self) -> TestResult:
        """Test invalid endpoints return 404."""
        print("❌ Testing invalid endpoint handling...")
        
        result = self._make_request("GET", "/nonexistent/endpoint")
        
        if result.status_code == 404:
            print(f"  ✅ 404 correctly returned for invalid endpoint ({result.response_time:.2f}s)")
            result.success = True  # Expected behavior
        else:
            print(f"  ❌ Expected 404, got {result.status_code}")
            result.success = False
        
        return result
    
    def test_invalid_json(self) -> TestResult:
        """Test invalid JSON handling."""
        print("🚫 Testing invalid JSON handling...")
        
        result = self._make_request("POST", "/agent/chat",
                                  data="invalid json{",
                                  headers={"Content-Type": "application/json"})
        
        if result.status_code == 422:  # FastAPI validation error
            print(f"  ✅ JSON validation error correctly returned ({result.response_time:.2f}s)")
            result.success = True  # Expected behavior
        else:
            print(f"  ❌ Expected 422, got {result.status_code}")
        
        return result
    
    # =====================================
    # CLEANUP AND REPORTING
    # =====================================
    
    def cleanup_sessions(self):
        """Clean up test sessions."""
        print("🧹 Cleaning up test sessions...")
        
        for session_id in self.session_ids:
            try:
                result = self._make_request("DELETE", f"/sessions/{session_id}")
                if result.success:
                    print(f"  ✅ Deleted session {session_id[:8]}...")
                else:
                    print(f"  ⚠️ Failed to delete session {session_id[:8]}...")
            except:
                pass
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        print("🚀 Starting comprehensive API regression tests...\n")
        
        test_methods = [
            # Health and info
            self.test_health_endpoint,
            self.test_root_endpoint,
            
            # Agent endpoints
            self.test_agent_stats,
            self.test_agent_query,
            self.test_agent_chat,
            self.test_agent_chat_with_session,
            
            # Session endpoints
            self.test_session_create,
            self.test_session_info,
            self.test_session_stats,
            
            # MCP endpoints
            self.test_mcp_plan_query,
            self.test_mcp_query_guidelines,
            self.test_mcp_summarize,
            
            # Error handling
            self.test_invalid_endpoints,
            self.test_invalid_json,
        ]
        
        # Run all tests
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"  💥 Test {test_method.__name__} crashed: {e}")
            print()  # Add spacing
        
        # Cleanup
        self.cleanup_sessions()
        
        # Generate report
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        
        avg_response_time = sum(r.response_time for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
                "avg_response_time": f"{avg_response_time:.2f}s"
            },
            "failed_tests": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "status_code": r.status_code,
                    "error": r.error_message
                }
                for r in self.test_results if not r.success
            ],
            "slowest_endpoints": sorted([
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "response_time": f"{r.response_time:.2f}s"
                }
                for r in self.test_results if r.success
            ], key=lambda x: float(x["response_time"][:-1]), reverse=True)[:5]
        }
        
        return report


def main():
    """Run regression tests and display results."""
    print("=" * 60)
    print("🧪 GUIDELINES AGENT API REGRESSION TESTS")
    print("=" * 60)
    print()
    
    # Check server availability
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not healthy at {BASE_URL}")
            return
    except:
        print(f"❌ Server not accessible at {BASE_URL}")
        print("   Please ensure the server is running with: ./start_server.sh")
        return
    
    # Run tests
    tester = GuidelinesAgentTester(BASE_URL)
    report = tester.run_all_tests()
    
    # Display results
    print("=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    summary = report["summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Success Rate: {summary['success_rate']}")
    print(f"Average Response Time: {summary['avg_response_time']}")
    
    if report["failed_tests"]:
        print("\n❌ FAILED TESTS:")
        for test in report["failed_tests"]:
            print(f"  • {test['method']} {test['endpoint']} - {test['error']}")
    
    if report["slowest_endpoints"]:
        print(f"\n⏱️ SLOWEST ENDPOINTS:")
        for endpoint in report["slowest_endpoints"]:
            print(f"  • {endpoint['method']} {endpoint['endpoint']} - {endpoint['response_time']}")
    
    print("\n" + "=" * 60)
    
    # Return appropriate exit code
    return 0 if summary['failed'] == 0 else 1


if __name__ == "__main__":
    exit(main())