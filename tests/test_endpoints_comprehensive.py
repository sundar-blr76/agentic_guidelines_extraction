"""
Comprehensive endpoint testing for the Guidelines Agent API

This test suite validates all major endpoints and their integration:
1. Health checks
2. Session management  
3. Document ingestion
4. Agent chat/query
5. System statistics
"""

import pytest
import requests
import os
import time
from pathlib import Path

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_PDF_PATH = "test_guidelines.pdf"

class TestEndpointsComprehensive:
    """Comprehensive API endpoint testing"""
    
    def setup(self):
        """Setup test environment"""
        self.base_url = API_BASE_URL
        self.session_id = None
        
        # Check if test PDF exists
        self.test_pdf_exists = os.path.exists(TEST_PDF_PATH)
        if self.test_pdf_exists:
            print(f"✅ Test PDF found: {TEST_PDF_PATH}")
        else:
            print(f"⚠️ Test PDF not found: {TEST_PDF_PATH}")
        
        return self
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"✅ Health check: {data}")
    
    def test_session_creation(self):
        """Test session creation"""
        response = requests.post(f"{self.base_url}/sessions", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "session_id" in data
        self.session_id = data["session_id"]
        print(f"✅ Session created: {self.session_id}")
    
    def test_session_list(self):
        """Test getting session list"""
        response = requests.get(f"{self.base_url}/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        print(f"✅ Sessions retrieved: {data.get('stats', {})}")
    
    def test_agent_chat_basic(self):
        """Test basic chat functionality"""
        if not self.session_id:
            self.test_session_creation()
        
        chat_data = {
            "message": "Hello, can you help me with investment guidelines?",
            "session_id": self.session_id
        }
        
        response = requests.post(f"{self.base_url}/agent/chat", json=chat_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "response" in data
        assert len(data["response"]) > 0
        print(f"✅ Chat response received: {data['response'][:100]}...")
    
    def test_agent_query_guideline_search(self):
        """Test guideline search functionality"""
        if not self.session_id:
            self.test_session_creation()
        
        chat_data = {
            "message": "Show me all portfolios with investment guidelines",
            "session_id": self.session_id
        }
        
        response = requests.post(f"{self.base_url}/agent/chat", json=chat_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print(f"✅ Guideline search completed")
    
    def test_document_ingestion_success(self):
        """Test successful document ingestion"""
        if not self.test_pdf_exists:
            print("⏭️ Skipping document ingestion test - no PDF file found")
            return
            
        with open(TEST_PDF_PATH, 'rb') as f:
            files = {'file': (TEST_PDF_PATH, f, 'application/pdf')}
            
            print(f"📄 Starting document ingestion: {TEST_PDF_PATH}")
            start_time = time.time()
            
            response = requests.post(f"{self.base_url}/agent/ingest", files=files)
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert response.status_code == 200
            data = response.json()
            
            print(f"⏱️ Ingestion took {duration:.2f} seconds")
            print(f"📊 Ingestion result: {data}")
            
            # Validate response structure
            assert data["success"] == True
            assert "message" in data
            
            # If successful, should have additional data
            if data["success"]:
                print(f"✅ Document ingested successfully!")
                print(f"  - Doc ID: {data.get('doc_id')}")
                print(f"  - Portfolio ID: {data.get('portfolio_id')}")
                print(f"  - Guidelines extracted: {data.get('guidelines_count', 0)}")
                print(f"  - Embeddings generated: {data.get('embeddings_generated', 0)}")
                print(f"  - Validation: {data.get('validation_summary', 'N/A')}")
    
    def test_document_ingestion_invalid_file(self):
        """Test document ingestion with invalid file"""
        # Create a fake text file
        fake_content = b"This is not a PDF file"
        files = {'file': ('fake.txt', fake_content, 'text/plain')}
        
        response = requests.post(f"{self.base_url}/agent/ingest", files=files)
        assert response.status_code == 400
        print("✅ Invalid file type correctly rejected")
    
    def test_system_stats(self):
        """Test system statistics endpoint"""
        response = requests.get(f"{self.base_url}/agent/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "stats" in data
        
        stats = data["stats"]
        print(f"✅ System stats retrieved:")
        print(f"  - Total portfolios: {stats.get('total_portfolios', 0)}")
        print(f"  - Total guidelines: {stats.get('total_guidelines', 0)}")
        print(f"  - Needs embeddings: {stats.get('needs_embeddings', False)}")
    
    def test_environment_and_providers(self):
        """Test environment configuration and LLM providers"""
        # This would test a hypothetical config endpoint
        try:
            response = requests.get(f"{self.base_url}/config")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Environment config: {data}")
            else:
                print("⚠️ Config endpoint not available")
        except:
            print("⚠️ Config endpoint not implemented")
    
    def test_conversation_flow(self):
        """Test complete conversation flow"""
        if not self.session_id:
            self.test_session_creation()
        
        # Multi-turn conversation
        messages = [
            "What portfolios do you have?",
            "Tell me about investment restrictions",
            "What are the asset allocation limits?"
        ]
        
        for i, message in enumerate(messages, 1):
            chat_data = {
                "message": message,
                "session_id": self.session_id
            }
            
            response = requests.post(f"{self.base_url}/agent/chat", json=chat_data)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            
            print(f"✅ Turn {i}: {message}")
            print(f"  Response: {data['response'][:150]}...")
    
    def test_error_handling(self):
        """Test error handling for various scenarios"""
        
        # Test invalid session ID
        chat_data = {
            "message": "Hello",
            "session_id": "invalid-session-id"
        }
        
        response = requests.post(f"{self.base_url}/agent/chat", json=chat_data)
        # Should either work (create session) or return appropriate error
        print(f"✅ Invalid session handling: {response.status_code}")
        
        # Test empty message
        chat_data = {
            "message": "",
            "session_id": self.session_id
        }
        
        response = requests.post(f"{self.base_url}/agent/chat", json=chat_data)
        print(f"✅ Empty message handling: {response.status_code}")
    
    def test_performance_metrics(self):
        """Test basic performance metrics"""
        if not self.session_id:
            self.test_session_creation()
        
        start_time = time.time()
        
        chat_data = {
            "message": "Quick test message",
            "session_id": self.session_id
        }
        
        response = requests.post(f"{self.base_url}/agent/chat", json=chat_data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        print(f"✅ Chat response time: {response_time:.2f} seconds")
        
        # Basic performance assertion (should respond within reasonable time)
        assert response_time < 30.0, f"Response too slow: {response_time} seconds"


def run_comprehensive_tests():
    """Run all comprehensive tests manually"""
    print("🚀 Starting Comprehensive API Tests")
    print("="*50)
    
    test_suite = TestEndpointsComprehensive()
    test_suite.setup()
    
    tests = [
        ("Health Check", test_suite.test_health_endpoint),
        ("Session Management", test_suite.test_session_creation),
        ("Session List", test_suite.test_session_list),
        ("Basic Chat", test_suite.test_agent_chat_basic),
        ("Guideline Search", test_suite.test_agent_query_guideline_search),
        ("Document Ingestion", test_suite.test_document_ingestion_success),
        ("Invalid File Upload", test_suite.test_document_ingestion_invalid_file),
        ("System Statistics", test_suite.test_system_stats),
        ("Environment Config", test_suite.test_environment_and_providers),
        ("Conversation Flow", test_suite.test_conversation_flow),
        ("Error Handling", test_suite.test_error_handling),
        ("Performance Metrics", test_suite.test_performance_metrics),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            test_func()
            passed += 1
            print(f"✅ PASSED: {test_name}")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED: {test_name} - {str(e)}")
    
    print(f"\n📊 Test Results:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    return passed, failed


if __name__ == "__main__":
    run_comprehensive_tests()