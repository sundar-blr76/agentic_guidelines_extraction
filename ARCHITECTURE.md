# Architecture Documentation

## Overview

This application follows a clean **MVC-like architecture** with clear separation of concerns:

- **API Layer** (`api/`) - HTTP endpoints, request/response handling
- **Service Layer** (`services/`) - Business logic and orchestration  
- **Model Layer** (`models/`) - Data entities and repository pattern
- **Agent Layer** (`agents/`) - AI-specific logic and LangChain integration

## Architecture Principles

### 1. **Separation of Concerns**
Each layer has a single, well-defined responsibility:

```
┌─────────────────┐
│   API Layer     │ ← HTTP, validation, serialization
├─────────────────┤  
│ Service Layer   │ ← Business logic, orchestration
├─────────────────┤
│  Model Layer    │ ← Data access, persistence
└─────────────────┘
```

### 2. **Dependency Injection**
Services are injected via FastAPI dependencies, making testing and mocking easy.

### 3. **Repository Pattern**
All database access goes through repository classes with consistent interfaces.

### 4. **Single Responsibility**
Each service/repository has one clear purpose and minimal dependencies.

## Layer Details

### API Layer (`api/`)

**Purpose**: Handle HTTP requests, validate input, format responses

**Structure**:
```
api/
├── routes/
│   ├── agent_routes.py    # /agent/* - User-facing endpoints
│   ├── session_routes.py  # /sessions/* - Session management
│   └── mcp_routes.py      # /mcp/* - Internal agent tools
├── schemas/               # Pydantic models
│   ├── common_schemas.py  # Shared response formats
│   └── agent_schemas.py   # Agent-specific schemas
└── middleware/            # Custom middleware (future)
```

**Key Endpoints**:
- `POST /agent/query` - Natural language queries
- `POST /agent/chat` - Session-based conversations
- `POST /agent/ingest` - Document upload and processing
- `POST /sessions/` - Create new session
- `POST /mcp/plan_query` - Internal: query planning
- `POST /mcp/query_guidelines` - Internal: search guidelines

### Service Layer (`services/`)

**Purpose**: Business logic, complex operations, orchestration

**Services**:

1. **DocumentService** - Document extraction and validation
   - Extract guidelines from PDFs
   - Validate extraction results
   - Handle document lifecycle

2. **GuidelineService** - Guideline processing and search
   - Save portfolios, documents, guidelines
   - Semantic and text search
   - Generate missing embeddings

3. **AgentService** - AI agent orchestration
   - Manage query and ingestion agents
   - Process high-level user requests
   - Handle file uploads

4. **SessionService** - Session management
   - Create/manage user sessions
   - Track conversation history
   - Context management

### Model Layer (`models/`)

**Purpose**: Data entities, database access, business rules

**Structure**:
```
models/
├── entities/              # Business entities
│   └── portfolio.py       # Portfolio, Document, Guideline classes
├── repositories/          # Data access objects
│   ├── base_repository.py # Common database operations
│   ├── portfolio_repository.py
│   ├── document_repository.py
│   └── guideline_repository.py
└── database.py            # Connection management
```

**Entities**:
- `Portfolio` - Investment funds
- `Document` - Source PDF documents  
- `Guideline` - Individual investment rules
- `GuidelineSearchResult` - Search results with ranking

**Repository Pattern**:
Each repository provides:
- `create()` - Insert new records
- `get_by_id()` - Find by primary key
- `update()` - Modify existing records  
- `delete()` - Remove records
- Custom query methods (e.g., `semantic_search()`)

### Agent Layer (`agents/`)

**Purpose**: AI-specific logic, LangChain integration

Currently uses existing `agent/agent_main.py` - future refactoring will move this to the new structure.

## Data Flow Examples

### 1. User Query Processing

```
POST /agent/query
    ↓
agent_routes.py → AgentService.process_query()
    ↓  
create_query_agent() → LangChain tools
    ↓
GuidelineService.search_guidelines()
    ↓
GuidelineRepository.semantic_search()
    ↓
PostgreSQL with vector similarity
```

### 2. Document Ingestion

```
POST /agent/ingest (PDF file)
    ↓
agent_routes.py → AgentService.process_file_upload_ingestion()
    ↓
DocumentService.extract_guidelines_from_pdf()
    ↓  
GuidelineService.process_full_extraction()
    ↓
PortfolioRepo.create() + DocumentRepo.create() + GuidelineRepo.create_batch()
    ↓
GuidelineService.generate_missing_embeddings()
```

## Database Schema

```sql
-- Core entities
portfolio (portfolio_id, portfolio_name)
document (doc_id, portfolio_id, doc_name, doc_date, digest)  
guideline (portfolio_id, rule_id, doc_id, text, embedding, ...)

-- Vector similarity search
SELECT * FROM guideline 
WHERE (1 - (embedding <=> query_vector)) >= threshold
ORDER BY similarity DESC;
```

## Testing Strategy

### Unit Tests
- **Repositories**: Mock database connections
- **Services**: Mock repository dependencies  
- **API Routes**: Mock service dependencies

### Integration Tests  
- **Database**: Use test database with real connections
- **API**: Full request/response cycle testing
- **Agent**: Test LangChain tool integration

## Migration from Old Architecture

The old `mcp_server/main.py` (290 lines) has been split into:

- **3 route files** (150 lines total) - focused endpoints
- **4 service files** (400 lines total) - business logic  
- **4 repository files** (300 lines total) - data access
- **Entity models** (100 lines) - business objects

**Benefits**:
- **Testability**: Each component can be tested independently
- **Maintainability**: Clear boundaries, easier to modify
- **Scalability**: Services can become microservices later
- **Developer Experience**: Clear structure for new team members

## Performance Considerations

1. **Database Connection Pooling**: DatabaseManager handles connections efficiently
2. **Batch Operations**: `GuidelineRepository.create_batch()` for bulk inserts
3. **Vector Search Optimization**: Uses PostgreSQL pgvector extension
4. **Caching**: Future - add Redis for frequently accessed data

## Security Considerations

1. **Input Validation**: Pydantic schemas validate all inputs
2. **SQL Injection**: Parameterized queries in all repositories
3. **File Upload**: Temporary files, size limits (future)
4. **Authentication**: JWT tokens (future enhancement)

## Future Enhancements

1. **Dependency Injection**: FastAPI dependencies for services
2. **Event System**: Publish/subscribe for decoupling
3. **Background Tasks**: Celery for long-running operations
4. **API Versioning**: Support multiple API versions
5. **Metrics**: Prometheus/Grafana monitoring
6. **Rate Limiting**: Protect against abuse