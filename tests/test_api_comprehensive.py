#!/usr/bin/env python3
"""
Comprehensive API Testing Suite
================================

Tests all endpoints of the Guidelines Agent API with proper error handling
and detailed reporting.

Usage:
    python test_api_comprehensive.py [--host localhost] [--port 8000] [--verbose]
"""

import requests
import json
import time
import sys
import argparse
from typing import Dict, List, Any, Optional
import os
from datetime import datetime

class APITester:
    def __init__(self, host: str = "localhost", port: int = 8000, verbose: bool = False):
        self.base_url = f"http://{host}:{port}"
        self.verbose = verbose
        self.test_session_id = f"test-session-{int(time.time())}"
        self.test_results = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def verbose_log(self, message: str):
        """Log message only in verbose mode"""
        if self.verbose:
            self.log(message, "DEBUG")
    
    def test_endpoint(self, name: str, method: str, endpoint: str, 
                     data: Any = None, files: Dict = None, 
                     expected_status: int = 200, timeout: int = 30) -> Dict[str, Any]:
        """Test a single endpoint and return results"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        self.verbose_log(f"Testing {name}: {method} {url}")
        if data and self.verbose:
            self.verbose_log(f"Request data: {json.dumps(data, indent=2)}")
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, data=data, files=files, timeout=timeout)
                else:
                    headers = {"Content-Type": "application/json"} if data else {}
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            elapsed_time = time.time() - start_time
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            result = {
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": response.status_code == expected_status,
                "response_time": round(elapsed_time, 2),
                "response_data": response_data
            }
            
            if result["success"]:
                self.log(f"✅ {name}: PASSED ({result['response_time']}s)")
            else:
                self.log(f"❌ {name}: FAILED - Expected {expected_status}, got {response.status_code}")
                self.verbose_log(f"Response: {json.dumps(response_data, indent=2)}")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.log(f"❌ {name}: ERROR - {str(e)}")
            result = {
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "status_code": None,
                "expected_status": expected_status,
                "success": False,
                "response_time": round(elapsed_time, 2),
                "error": str(e)
            }
            self.test_results.append(result)
            return result
    
    def run_health_tests(self):
        """Test health and basic endpoints"""
        self.log("=== Running Health Tests ===")
        
        self.test_endpoint(
            name="Health Check",
            method="GET", 
            endpoint="/health"
        )
    
    def run_session_tests(self):
        """Test session management endpoints"""
        self.log("=== Running Session Tests ===")
        
        # Get sessions list
        self.test_endpoint(
            name="List Sessions",
            method="GET",
            endpoint="/sessions"
        )
        
        # Create new session
        result = self.test_endpoint(
            name="Create Session",
            method="POST",
            endpoint="/sessions",
            data={"session_id": self.test_session_id}
        )
        
        # Check if session was created
        if result["success"] and "session_id" in result["response_data"]:
            created_session_id = result["response_data"]["session_id"]
            self.verbose_log(f"Created session: {created_session_id}")
    
    def run_document_tests(self):
        """Test document ingestion endpoints"""
        self.log("=== Running Document Tests ===")
        
        # Check if test PDF exists
        test_pdf_path = "test_guidelines.pdf"
        if not os.path.exists(test_pdf_path):
            self.log(f"⚠️ Warning: {test_pdf_path} not found, skipping document ingestion tests")
            return
        
        # Test document ingestion
        with open(test_pdf_path, 'rb') as pdf_file:
            files = {'file': ('test_guidelines.pdf', pdf_file, 'application/pdf')}
            data = {'session_id': self.test_session_id}
            
            result = self.test_endpoint(
                name="Document Ingestion",
                method="POST",
                endpoint="/agent/ingest",
                data=data,
                files=files,
                timeout=120  # Document processing can take time
            )
            
            # Store doc_id for later tests
            if result["success"] and "doc_id" in result.get("response_data", {}):
                self.doc_id = result["response_data"]["doc_id"]
                self.verbose_log(f"Ingested document ID: {self.doc_id}")
    
    def run_query_tests(self):
        """Test query/chat endpoints"""
        self.log("=== Running Query Tests ===")
        
        test_queries = [
            "Hello",
            "What are the risk management guidelines?",
            "Tell me about investment restrictions",
            "What are the portfolio diversification requirements?"
        ]
        
        for query in test_queries:
            result = self.test_endpoint(
                name=f"Query: '{query[:30]}...'",
                method="POST",
                endpoint="/agent/chat",
                data={
                    "message": query,
                    "session_id": self.test_session_id
                },
                timeout=60  # Queries can take time
            )
            
            # Brief pause between queries
            time.sleep(1)
    
    def run_guideline_tests(self):
        """Test guideline search and retrieval endpoints"""
        self.log("=== Running Guideline Tests ===")
        
        # Test search functionality
        self.test_endpoint(
            name="Guideline Search",
            method="POST",
            endpoint="/guidelines/search",
            data={
                "query": "risk management",
                "limit": 10
            }
        )
        
        # Test stats endpoint
        self.test_endpoint(
            name="Guidelines Stats",
            method="GET",
            endpoint="/guidelines/stats"
        )
    
    def run_performance_tests(self):
        """Run basic performance tests"""
        self.log("=== Running Performance Tests ===")
        
        # Test multiple health checks
        start_time = time.time()
        for i in range(5):
            self.test_endpoint(
                name=f"Performance Test #{i+1}",
                method="GET",
                endpoint="/health"
            )
        
        total_time = time.time() - start_time
        avg_time = total_time / 5
        self.log(f"Average response time for 5 health checks: {avg_time:.2f}s")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        # Calculate average response time
        response_times = [r["response_time"] for r in self.test_results if "response_time" in r]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Group failures by type
        failures = [r for r in self.test_results if not r["success"]]
        
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0,
                "average_response_time": round(avg_response_time, 2)
            },
            "failures": failures,
            "all_results": self.test_results
        }
        
        return report
    
    def print_summary(self):
        """Print test summary"""
        report = self.generate_report()
        summary = report["test_summary"]
        
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"Total Tests:      {summary['total_tests']}")
        print(f"Passed:           {summary['passed']} ✅")
        print(f"Failed:           {summary['failed']} ❌")
        print(f"Success Rate:     {summary['success_rate']}%")
        print(f"Avg Response:     {summary['average_response_time']}s")
        
        if report["failures"]:
            print("\nFAILURES:")
            for failure in report["failures"]:
                status = failure.get("status_code", "ERROR")
                error = failure.get("error", "Unknown error")
                print(f"  ❌ {failure['name']}: {status} - {error}")
        
        # Overall status
        if summary["failed"] == 0:
            print(f"\n🎉 ALL TESTS PASSED! System is fully functional.")
            return 0
        elif summary["success_rate"] >= 80:
            print(f"\n⚠️ Most tests passed ({summary['success_rate']}%). Some issues detected.")
            return 1
        else:
            print(f"\n🚨 Many tests failed ({summary['success_rate']}% success). System has significant issues.")
            return 2
    
    def run_all_tests(self):
        """Run complete test suite"""
        self.log("Starting comprehensive API test suite...")
        
        try:
            self.run_health_tests()
            self.run_session_tests()
            self.run_document_tests()
            self.run_query_tests()
            self.run_guideline_tests()
            
            if not self.verbose:  # Only run performance tests in non-verbose mode
                self.run_performance_tests()
            
        except KeyboardInterrupt:
            self.log("Tests interrupted by user")
            return 130
        except Exception as e:
            self.log(f"Test suite error: {e}")
            return 1
        
        return self.print_summary()


def main():
    parser = argparse.ArgumentParser(description="Comprehensive API Testing Suite")
    parser.add_argument("--host", default="localhost", help="API host (default: localhost)")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--save-report", help="Save JSON report to file")
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = APITester(host=args.host, port=args.port, verbose=args.verbose)
    
    # Run tests
    exit_code = tester.run_all_tests()
    
    # Save report if requested
    if args.save_report:
        report = tester.generate_report()
        with open(args.save_report, 'w') as f:
            json.dump(report, f, indent=2)
        tester.log(f"Report saved to {args.save_report}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()