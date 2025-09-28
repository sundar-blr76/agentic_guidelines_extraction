# Guidelines Agent - Investment Guidelines Extraction and Querying System

## Overview

An AI-powered application that extracts investment guidelines from PDF documents and enables natural language querying. Built with a clean **MVC architecture** using FastAPI, PostgreSQL, and Google's Gemini AI models.

### Key Features

- 🤖 **AI-Powered Extraction**: Automatically extract structured investment guidelines from PDF documents
- 🔍 **Semantic Search**: Query guidelines using natural language with vector similarity search  
- 💬 **Session-Based Chat**: Stateful conversations with context awareness
- 🏗️ **Clean Architecture**: Well-organized MVC structure for maintainability
- 📊 **Vector Database**: PostgreSQL with pgvector for efficient similarity search
- 🚀 **FastAPI**: Modern, fast Python web framework with automatic API documentation

## Architecture

```
┌─────────────────┐
│   Frontend      │ ← React + TypeScript UI
│   (Port 3000)   │
└─────────┬───────┘
          │ HTTP
┌─────────▼───────┐
│   API Layer     │ ← FastAPI routes (/agent, /sessions, /mcp)  
├─────────────────┤
│ Service Layer   │ ← Business logic (Document, Guideline, Agent services)
├─────────────────┤
│  Model Layer    │ ← Repository pattern + PostgreSQL with pgvector
└─────────────────┘
```

### Core Components

- **Document Service**: PDF processing and guideline extraction
- **Guideline Service**: Search, persistence, and embedding generation
- **Agent Service**: AI agent orchestration and high-level operations
- **Session Service**: User session and conversation management

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- Node.js 18+ (for frontend)
- Google Gemini API key

### 2. Environment Setup

```bash
# Clone and setup
git clone <repository>
cd agentic_guidelines_extraction

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-gemini-api-key"
```

### 3. Database Setup

```bash
# Configure database in guidelines_agent/core/config.py
# Default: PostgreSQL on 192.168.29.69:5432

# Run database setup
cd guidelines_agent/core
python3 setup_database.py
```

### 4. Start the Application

**Recommended: Use our server management scripts**

```bash
# Complete server restart with verification (recommended)
./restart_servers.sh

# Fast daily development restart
./quick_restart.sh

# Backend only (API development)
./restart_servers.sh --backend-only

# Frontend only (UI development)  
./restart_servers.sh --frontend-only
```

**Manual startup (alternative):**

```bash
# Start backend (from project root)
./start_server.sh

# Start frontend (in another terminal)
./start_frontend.sh
```

> 💡 **Tip**: Use `./show_usage.sh` for complete script documentation and development workflow guide.

### 5. Verify Installation

**Automated verification:**

```bash
# Complete health check and testing
./comprehensive_test.sh

# Quick smoke test
./test_quick.sh

# Check server status
./restart_servers.sh --status
```

**Manual verification:**

```bash
# Test API
curl http://localhost:8000/health

# Access frontend
open http://localhost:3000

# View API docs  
open http://localhost:8000/docs
```

## API Endpoints

### User-Facing Endpoints (`/agent`)

- `POST /agent/query` - Ask questions about guidelines
- `POST /agent/chat` - Conversational interface  
- `POST /agent/ingest` - Upload PDF documents
- `GET /agent/stats` - System statistics

### Session Management (`/sessions`)

- `POST /sessions` - Create new session
- `GET /sessions/{id}` - Get session info
- `GET /sessions/{id}/history` - Conversation history
- `DELETE /sessions/{id}` - Delete session

### Internal Tools (`/mcp`)

- `POST /mcp/plan_query` - Query planning
- `POST /mcp/query_guidelines` - Search guidelines
- `POST /mcp/summarize` - Summarize results
- `POST /mcp/extract_guidelines` - Extract from PDF

## CLI Usage

The system also provides CLI commands for batch operations:

```bash
# Extract guidelines from PDF
python3 cli.py extract-guidelines sample_docs/document.pdf

# Persist extracted guidelines  
python3 cli.py persist-guidelines results/document.json

# Generate embeddings for search
python3 cli.py stamp-embedding

# Query guidelines
python3 cli.py query "What are the rebalancing requirements?"
```

## Usage Examples

### 1. Document Ingestion

```python
import requests

# Upload PDF document
with open("investment_policy.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/agent/ingest",
        files={"file": f}
    )
    
result = response.json()
print(f"Extracted {result['guidelines_count']} guidelines")
```

### 2. Natural Language Queries

```python
# Ask questions about guidelines
response = requests.post(
    "http://localhost:8000/agent/query",
    json={
        "query": "What are the rebalancing requirements for equity funds?",
        "portfolio_ids": ["retirement-2025"]  # Optional filter
    }
)

answer = response.json()["response"]
print(answer)
```

### 3. Session-Based Conversations

```python
# Start conversation
response = requests.post(
    "http://localhost:8000/agent/chat",
    json={"message": "Tell me about Fund ABC"}
)

session_id = response.json()["session_id"]

# Continue conversation with context
response = requests.post(
    "http://localhost:8000/agent/chat", 
    json={
        "message": "What are its investment restrictions?",
        "session_id": session_id
    }
)
```

## Development

### Project Structure

```
guidelines_agent/
├── api/                    # API layer
│   ├── routes/            # FastAPI route handlers
│   ├── schemas/           # Pydantic models
│   └── middleware/        # Custom middleware
├── services/              # Business logic layer
│   ├── document_service.py
│   ├── guideline_service.py
│   ├── agent_service.py
│   └── session_service.py
├── models/                # Data layer
│   ├── entities/         # Business entities
│   └── repositories/     # Data access objects
├── core/                 # Legacy core utilities
└── main.py              # FastAPI application
```

### Running Tests

**Comprehensive testing:**

```bash
# Complete test suite with server health checks
./comprehensive_test.sh

# Quick regression tests
./test_quick.sh

# API endpoint testing  
./test_comprehensive_api.sh
```

**Traditional pytest:**

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test
python3 -m pytest tests/test_api.py -v

# Run with coverage
python3 -m pytest --cov=guidelines_agent tests/
```

### Database Schema

```sql
-- Core entities
portfolio (portfolio_id, portfolio_name)
document (doc_id, portfolio_id, doc_name, doc_date, digest)
guideline (portfolio_id, rule_id, doc_id, text, embedding, provenance)

-- Vector search capabilities
CREATE INDEX ON guideline USING ivfflat (embedding vector_cosine_ops);
```

### Adding New Features

1. **New API Endpoint**: Add route in appropriate `api/routes/` file
2. **Business Logic**: Add methods to relevant service in `services/`
3. **Data Access**: Add repository methods in `models/repositories/`
4. **Database Changes**: Update `core/schema.sql` and migration scripts

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your-gemini-api-key

# Optional  
DB_HOST=192.168.29.69      # Database host
DB_PORT=5432               # Database port
DB_NAME=guidelines         # Database name
DB_USER=postgres           # Database user
DB_PASSWORD=postgres       # Database password
```

### Model Configuration

Models can be changed in service files:
- Document extraction: `services/document_service.py`
- Query processing: `agent/agent_main.py` 
- Summarization: `core/summarize.py`

Current models:
- **Main Agent**: `gemini-pro-latest`
- **Summarization**: `gemini-2.5-flash`
- **Embeddings**: `models/embedding-001`

## Monitoring and Logging

### Logs

- Application logs: `logs/api_server.log`
- Custom IST timestamps with structured logging
- Error tracking with full stack traces

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# System statistics
curl http://localhost:8000/agent/stats
```

## Deployment

### Production Setup

1. **Database**: Use managed PostgreSQL with pgvector
2. **Secrets**: Store API keys in secure vault
3. **Scaling**: Use multiple uvicorn workers
4. **Monitoring**: Add Prometheus metrics
5. **Caching**: Add Redis for sessions and embeddings

### Docker Deployment (Future)

```bash
# Build and run
docker build -t guidelines-agent .
docker run -p 8000:8000 guidelines-agent
```

## Troubleshooting

### Common Issues

1. **Model Not Found**: Update model names in configuration files
2. **Database Connection**: Check PostgreSQL setup and pgvector extension
3. **Import Errors**: Ensure virtual environment is activated
4. **Memory Issues**: Large PDFs may require more memory for extraction

### Debug Mode

```bash
# Run with debug logging
uvicorn guidelines_agent.main:app --log-level debug --reload
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Follow the existing architecture patterns
4. Add tests for new functionality  
5. Submit pull request with clear description

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Documentation

- [Script Documentation](SCRIPT_DOCUMENTATION.md) - Complete development scripts guide
- [Architecture Documentation](ARCHITECTURE.md) - Detailed system architecture
- [API Documentation](API.md) - Complete API reference  
- [Development Guide](RUNBOOK.md) - Setup and development instructions

---

**Version**: 2.0.0  
**Last Updated**: January 2025