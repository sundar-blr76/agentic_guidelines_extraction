"""Base service class with common functionality."""
from abc import ABC
from guidelines_agent.models.repositories import (
    PortfolioRepository, 
    DocumentRepository, 
    GuidelineRepository
)
import logging

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base service class providing common repository access."""
    
    def __init__(self):
        self.portfolio_repo = PortfolioRepository()
        self.document_repo = DocumentRepository()
        self.guideline_repo = GuidelineRepository()
        self.logger = logger