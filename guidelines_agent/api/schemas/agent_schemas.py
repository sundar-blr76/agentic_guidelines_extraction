"""Pydantic schemas for agent-related API endpoints."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .common_schemas import SuccessResponse, ErrorResponse, SearchResult


# --- Request Schemas ---

class AgentQueryRequest(BaseModel):
    """Request schema for agent query endpoint."""
    query: str = Field(..., description="Natural language query")
    portfolio_ids: Optional[List[str]] = Field(None, description="Filter by portfolio IDs")
    session_id: Optional[str] = Field(None, description="Session ID for stateful queries")


class AgentChatRequest(BaseModel):
    """Request schema for agent chat endpoint."""
    message: str = Field(..., description="Chat message from user")
    session_id: Optional[str] = Field(None, description="Session ID for conversation")


class AgentInvokeRequest(BaseModel):
    """Request schema for general agent invocation."""
    action: str = Field(..., description="Action to perform (query, ingest, etc.)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")


# --- Response Schemas ---

class AgentQueryResponse(SuccessResponse):
    """Response schema for agent query."""
    response: Optional[str] = None
    session_id: Optional[str] = None
    search_results: Optional[List[SearchResult]] = None


class AgentChatResponse(SuccessResponse):
    """Response schema for agent chat."""
    response: str
    session_id: str


class AgentIngestionResponse(SuccessResponse):
    """Response schema for document ingestion."""
    doc_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    guidelines_count: Optional[int] = None
    embeddings_generated: Optional[int] = None
    validation_summary: Optional[str] = None


class AgentStatsResponse(SuccessResponse):
    """Response schema for system statistics."""
    stats: Optional[Dict[str, Any]] = None


# --- Internal Tool Schemas (MCP) ---

class PlanQueryInput(BaseModel):
    """Input for query planning tool."""
    user_query: str = Field(..., description="The natural language user query")


class PlanQueryOutput(BaseModel):
    """Output from query planning tool."""
    search_query: str
    summary_instruction: str
    top_k: int


class QueryGuidelinesInput(BaseModel):
    """Input for guideline querying tool."""
    query_text: str
    portfolio_id: Optional[str] = None
    top_k: int = 5


class SummarizeInput(BaseModel):
    """Input for summarization tool."""
    question: str
    sources: List[str]


class ExtractGuidelinesInput(BaseModel):
    """Input for guideline extraction tool."""
    pdf_bytes_base64: str
    doc_name: str


class ExtractGuidelinesOutput(BaseModel):
    """Output from guideline extraction."""
    is_valid: bool
    validation_summary: str
    guidelines: List[Dict[str, Any]]
    portfolio_info: Optional[Dict[str, Any]] = None


class PersistGuidelinesInput(BaseModel):
    """Input for persisting extracted guidelines."""
    data: Dict[str, Any]
    human_readable_digest: str


class StampEmbeddingInput(BaseModel):
    """Input for embedding generation."""
    doc_id: Optional[str] = None
    limit: Optional[int] = None