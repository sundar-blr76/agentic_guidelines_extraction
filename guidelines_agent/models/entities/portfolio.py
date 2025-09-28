"""Business entity models representing domain objects."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date
import json


@dataclass
class Portfolio:
    """Portfolio entity representing an investment fund."""
    portfolio_id: str
    portfolio_name: str
    
    def __post_init__(self):
        if not self.portfolio_id or not self.portfolio_name:
            raise ValueError("Portfolio ID and name are required")


@dataclass  
class Document:
    """Document entity representing a source document."""
    doc_id: str
    portfolio_id: str
    doc_name: str
    doc_date: Optional[date] = None
    human_readable_digest: Optional[str] = None
    
    def __post_init__(self):
        if not self.doc_id or not self.portfolio_id or not self.doc_name:
            raise ValueError("Document ID, portfolio ID, and name are required")


@dataclass
class Guideline:
    """Guideline entity representing an investment guideline."""
    portfolio_id: str
    rule_id: str
    doc_id: str
    text: str
    part: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    page: Optional[int] = None
    provenance: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if not self.portfolio_id or not self.rule_id or not self.doc_id or not self.text:
            raise ValueError("Portfolio ID, rule ID, document ID, and text are required")
    
    @property
    def full_provenance(self) -> str:
        """Generate human-readable provenance information."""
        parts = []
        if self.part:
            parts.append(f"Part {self.part}")
        if self.section:
            parts.append(f"Section {self.section}")
        if self.subsection:
            parts.append(f"Subsection {self.subsection}")
        if self.page:
            parts.append(f"Page {self.page}")
        
        base = ", ".join(parts) if parts else "Unknown location"
        if self.provenance:
            return f"{base} ({self.provenance})"
        return base
    
    def to_search_result(self, rank: int, similarity: Optional[float] = None) -> Dict[str, Any]:
        """Convert to search result format."""
        return {
            "rank": rank,
            "similarity": similarity,
            "portfolio_id": self.portfolio_id,
            "rule_id": self.rule_id,
            "guideline": self.text,
            "provenance": self.full_provenance
        }


@dataclass
class GuidelineSearchResult:
    """Search result for guideline queries."""
    guideline: Guideline
    rank: int
    similarity: Optional[float] = None
    portfolio_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API responses."""
        return {
            "rank": self.rank,
            "similarity": self.similarity,
            "portfolio_name": self.portfolio_name or "Unknown",
            "portfolio_id": self.guideline.portfolio_id,
            "rule_id": self.guideline.rule_id,
            "guideline": self.guideline.text,
            "provenance": self.guideline.full_provenance
        }


@dataclass
class ExtractionResult:
    """Result from document extraction process."""
    is_valid: bool
    validation_summary: str
    guidelines: List[Dict[str, Any]] = field(default_factory=list)
    portfolio_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "is_valid": self.is_valid,
            "validation_summary": self.validation_summary,
            "guidelines": self.guidelines,
            "portfolio_info": self.portfolio_info,
            "error_message": self.error_message
        }