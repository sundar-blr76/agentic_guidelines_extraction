"""
Test fixtures and utilities for the test suite.
"""
import json
import tempfile
import os
from typing import Dict, Any


# Sample test data
SAMPLE_PORTFOLIO = {
    "portfolio_id": "test-retirement-2025",
    "portfolio_name": "Test Retirement Fund 2025"
}

SAMPLE_DOCUMENT = {
    "doc_id": "test-doc-001",
    "portfolio_id": "test-retirement-2025",
    "doc_name": "Test Investment Policy Statement.pdf",
    "doc_date": "2024-01-01"
}

SAMPLE_GUIDELINE = {
    "portfolio_id": "test-retirement-2025",
    "rule_id": "test-rule-001",
    "doc_id": "test-doc-001",
    "text": "The fund shall maintain a minimum cash reserve of 5% of total assets.",
    "part": "III",
    "section": "A",
    "subsection": "1",
    "page": 15,
    "provenance": "Investment Guidelines Section"
}

SAMPLE_EXTRACTION_RESULT = {
    "is_valid": True,
    "validation_summary": "Valid Investment Policy Statement with 25 guidelines extracted",
    "guidelines": [
        {
            "rule_id": "rule-001",
            "text": "The fund shall diversify investments across asset classes.",
            "part": "III",
            "section": "A", 
            "page": 12
        },
        {
            "rule_id": "rule-002", 
            "text": "Maximum exposure to any single security is 5%.",
            "part": "III",
            "section": "B",
            "page": 13
        }
    ],
    "portfolio_info": {
        "portfolio_id": "test-portfolio-001",
        "portfolio_name": "Test Investment Fund"
    }
}

# API request/response examples
SAMPLE_CHAT_REQUEST = {
    "message": "What are the rebalancing requirements?"
}

SAMPLE_CHAT_RESPONSE = {
    "success": True,
    "response": "Based on the investment guidelines, rebalancing is required quarterly...",
    "session_id": "test-session-123",
    "message": "Chat processed successfully"
}

SAMPLE_QUERY_REQUEST = {
    "query": "What are the investment restrictions for equity funds?",
    "portfolio_ids": ["test-retirement-2025"]
}

SAMPLE_MCP_PLAN_REQUEST = {
    "user_query": "Tell me about risk management guidelines"
}

SAMPLE_MCP_PLAN_RESPONSE = {
    "search_query": "risk management guidelines portfolio",
    "summary_instruction": "Explain the risk management requirements and guidelines",
    "top_k": 10
}

SAMPLE_SESSION_CREATE_REQUEST = {
    "user_id": "test-user-123"
}


def create_temp_pdf() -> str:
    """Create a temporary PDF file for testing."""
    # Simple PDF content (minimal valid PDF)
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.write(pdf_content)
    temp_file.close()
    
    return temp_file.name


def cleanup_temp_file(filepath: str):
    """Clean up temporary test file."""
    if os.path.exists(filepath):
        os.unlink(filepath)


def save_test_results(results: Dict[str, Any], filename: str = "test_results.json"):
    """Save test results to file for analysis."""
    results_dir = os.path.join(os.path.dirname(__file__), "../results")
    os.makedirs(results_dir, exist_ok=True)
    
    filepath = os.path.join(results_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return filepath


def load_test_config() -> Dict[str, Any]:
    """Load test configuration."""
    return {
        "base_url": "http://localhost:8000",
        "timeout": 30,
        "max_retries": 3,
        "performance_thresholds": {
            "health_endpoint": 0.1,  # seconds
            "agent_query": 10.0,     # seconds  
            "agent_chat": 15.0,      # seconds
            "session_create": 1.0    # seconds
        }
    }