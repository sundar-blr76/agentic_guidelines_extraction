# Guidelines Agent API Documentation

## Overview

The Guidelines Agent API provides AI-powered investment guideline extraction and querying capabilities. The API is organized into three main endpoint groups:

- **`/agent/*`** - High-level user-facing operations
- **`/sessions/*`** - Session management for stateful conversations  
- **`/mcp/*`** - Internal tool endpoints used by AI agents

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. Future versions will implement JWT-based authentication.

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response  
```json
{
  "success": false,
  "error": "Error description",
  "details": { ... }
}
```

## Agent Endpoints (`/agent/*`)

These are the main user-facing endpoints for interacting with the AI agent.

### Query Guidelines

**POST** `/agent/query`

Process a natural language query about investment guidelines.

**Request Body:**
```json
{
  "query": "What are the rebalancing requirements for equity funds?",
  "portfolio_ids": ["fund-001"],  // Optional: filter by portfolios
  "session_id": "session-123"     // Optional: for stateful queries
}
```

**Response:**
```json
{
  "success": true,
  "response": "Based on the guidelines, equity funds must be rebalanced quarterly...",
  "session_id": "session-123",
  "message": "Query processed successfully"
}
```

### Chat with Agent

**POST** `/agent/chat`

Have a conversational chat with the agent using sessions.

**Request Body:**
```json
{
  "message": "Tell me about Fund ABC's investment restrictions",
  "session_id": "session-123"  // Optional: creates new session if not provided
}
```

**Response:**
```json
{
  "success": true,
  "response": "Fund ABC has the following investment restrictions...",
  "session_id": "session-123"
}
```

### Ingest Document

**POST** `/agent/ingest`

Upload and process a PDF document to extract investment guidelines.

**Request:** Multipart form data with PDF file

**Response:**
```json
{
  "success": true,
  "message": "Document ingestion completed successfully",
  "doc_id": "doc_20240101_120000",
  "portfolio_id": "retirement-2025",
  "guidelines_count": 45,
  "embeddings_generated": 45,
  "validation_summary": "Valid IPS document with 45 guidelines extracted"
}
```

### General Agent Invocation

**POST** `/agent/invoke`

General-purpose agent invocation for various actions.

**Request Body:**
```json
{
  "action": "ingest",  // or "stats"
  "parameters": {
    "pdf_path": "/path/to/document.pdf",
    "doc_name": "Investment Policy Statement"
  }
}
```

### Get System Statistics

**GET** `/agent/stats`

Get system-wide statistics and status.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_portfolios": 3,
    "total_guidelines": 150,
    "needs_embeddings": false,
    "portfolios": [
      {
        "portfolio_id": "retirement-2025",
        "portfolio_name": "OAS Retirement 2025",
        "guidelines_count": 45
      }
    ]
  }
}
```

## Session Endpoints (`/sessions/*`)

Manage user sessions for stateful conversations.

### Create Session

**POST** `/sessions`

Create a new user session.

**Request Body:**
```json
{
  "user_id": "user123"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "session-abc-123",
  "message": "Session created successfully"
}
```

### Get Session Info

**GET** `/sessions/{session_id}`

Get information about a specific session.

**Response:**
```json
{
  "success": true,
  "session": {
    "session_id": "session-abc-123",
    "user_id": "user123",
    "created_at": "2024-01-01T10:00:00Z",
    "last_activity": "2024-01-01T10:15:00Z",
    "interaction_count": 5,
    "context_summary": "Discussing Fund ABC investment restrictions",
    "conversation_history": "User asked about... Agent responded..."
  }
}
```

### Get Session History

**GET** `/sessions/{session_id}/history`

Get conversation history for a session.

**Query Parameters:**
- `limit` (optional): Number of recent interactions to return

**Response:**
```json
{
  "success": true,
  "session_id": "session-abc-123",
  "interactions": [
    {
      "timestamp": "2024-01-01T10:00:00Z",
      "query": "What are Fund ABC's restrictions?",
      "response": "Fund ABC has the following restrictions..."
    }
  ]
}
```

### Update Session Context

**PUT** `/sessions/{session_id}/context`

Update session context with new information.

**Request Body:**
```json
{
  "context_update": {
    "portfolio_id": "fund-001",
    "topic": "rebalancing rules",
    "preferences": {
      "detail_level": "high"
    }
  }
}
```

### Delete Session

**DELETE** `/sessions/{session_id}`

Delete a session and its history.

**Response:**
```json
{
  "success": true,
  "message": "Session session-abc-123 deleted"
}
```

### Get Session Statistics

**GET** `/sessions`

Get overall session statistics.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_sessions": 25,
    "active_sessions": 5,
    "sessions_last_hour": 10
  }
}
```

## MCP Endpoints (`/mcp/*`)

Internal tool endpoints used by AI agents. These are typically not called directly by users.

### Plan Query

**POST** `/mcp/plan_query`

Convert user query into search strategy and instructions.

**Request Body:**
```json
{
  "user_query": "What are the rebalancing rules for equity funds?"
}
```

**Response:**
```json
{
  "search_query": "rebalancing equity funds quarterly",
  "summary_instruction": "Explain the rebalancing requirements for equity funds",
  "top_k": 10
}
```

### Query Guidelines

**POST** `/mcp/query_guidelines`

Search guidelines using semantic or text search.

**Request Body:**
```json
{
  "query_text": "rebalancing quarterly equity",
  "portfolio_id": "fund-001",  // Optional
  "top_k": 5
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "rank": 1,
        "similarity": 0.85,
        "portfolio_name": "Equity Growth Fund",
        "portfolio_id": "fund-001",
        "rule_id": "rule_001",
        "guideline": "The fund must rebalance quarterly...",
        "provenance": "Part III, Section A, Page 15"
      }
    ],
    "total_found": 1
  }
}
```

### Summarize Guidelines

**POST** `/mcp/summarize`

Summarize search results to answer user question.

**Request Body:**
```json
{
  "question": "What are the rebalancing requirements?",
  "sources": [
    "The fund must rebalance quarterly when allocations drift more than 5%...",
    "Emergency rebalancing may occur if allocations exceed 10% drift..."
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": "**Direct Answer:** The fund requires quarterly rebalancing...",
    "sources_count": 2
  }
}
```

### Extract Guidelines

**POST** `/mcp/extract_guidelines`

Extract guidelines from PDF content (base64 encoded).

**Request Body:**
```json
{
  "pdf_bytes_base64": "JVBERi0xLjQK...",
  "doc_name": "Investment Policy Statement"
}
```

**Response:**
```json
{
  "is_valid": true,
  "validation_summary": "Valid IPS document",
  "guidelines": [
    {
      "rule_id": "rule_001",
      "text": "The fund shall maintain...",
      "part": "III",
      "section": "A",
      "page": 15
    }
  ],
  "portfolio_info": {
    "portfolio_id": "retirement-2025",
    "portfolio_name": "OAS Retirement 2025"
  }
}
```

### Persist Guidelines

**POST** `/mcp/persist_guidelines`

Save extracted guidelines to database.

**Request Body:**
```json
{
  "data": {
    "is_valid": true,
    "guidelines": [...],
    "portfolio_info": {...},
    "doc_name": "Investment Policy Statement"
  },
  "human_readable_digest": "Document summary..."
}
```

### Generate Embeddings

**POST** `/mcp/stamp_embedding`

Generate vector embeddings for guidelines without them.

**Request Body:**
```json
{
  "doc_id": "doc_20240101_120000",  // Optional: specific document
  "limit": 100                     // Optional: max guidelines to process
}
```

## Error Codes

- **400 Bad Request** - Invalid input or missing required fields
- **404 Not Found** - Resource (session, document) not found
- **500 Internal Server Error** - Server error, check logs

## Rate Limiting

Currently no rate limiting is implemented. Future versions will include rate limits per IP/user.

## SDK/Client Libraries

Currently no official SDKs available. Standard HTTP clients can be used.

**Example with curl:**
```bash
# Query guidelines
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the investment restrictions?"}'

# Upload document
curl -X POST http://localhost:8000/agent/ingest \
  -F "file=@document.pdf"
```

**Example with Python:**
```python
import requests

# Query guidelines
response = requests.post(
    "http://localhost:8000/agent/query",
    json={"query": "What are the investment restrictions?"}
)
result = response.json()

# Upload document  
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/agent/ingest",
        files={"file": f}
    )
```

## WebSocket Support

Not currently implemented. All interactions are via REST APIs.

## Changelog

- **v2.0.0** - Major architecture refactoring, improved API structure
- **v1.0.0** - Initial release with basic functionality