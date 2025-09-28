"""Common Pydantic schemas used across API endpoints."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SuccessResponse(BaseModel):
    """Standard success response format."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=10, ge=1, le=100, description="Items per page")


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PortfolioInfo(BaseModel):
    """Portfolio information schema."""
    portfolio_id: str
    portfolio_name: str


class DocumentInfo(BaseModel):
    """Document information schema."""
    doc_id: str
    doc_name: str
    doc_date: Optional[str] = None  # ISO date string
    portfolio_id: str


class GuidelineInfo(BaseModel):
    """Guideline information schema.""" 
    portfolio_id: str
    rule_id: str
    text: str
    provenance: Optional[str] = None


class SearchResult(BaseModel):
    """Search result item schema."""
    rank: int
    similarity: Optional[float] = None
    portfolio_name: str
    portfolio_id: str
    rule_id: str
    guideline: str
    provenance: str