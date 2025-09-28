"""
Unit tests for individual components using pytest fixtures.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from guidelines_agent.models.entities import Portfolio, Document, Guideline
from guidelines_agent.models.repositories import PortfolioRepository
from guidelines_agent.services import DocumentService, GuidelineService


class TestEntities:
    """Test business entity models."""
    
    def test_portfolio_creation(self):
        """Test Portfolio entity creation and validation."""
        portfolio = Portfolio(
            portfolio_id="test-001",
            portfolio_name="Test Portfolio"
        )
        
        assert portfolio.portfolio_id == "test-001"
        assert portfolio.portfolio_name == "Test Portfolio"
    
    def test_portfolio_validation(self):
        """Test Portfolio validation."""
        with pytest.raises(ValueError):
            Portfolio(portfolio_id="", portfolio_name="Test")
        
        with pytest.raises(ValueError):
            Portfolio(portfolio_id="test", portfolio_name="")
    
    def test_document_creation(self):
        """Test Document entity creation."""
        document = Document(
            doc_id="doc-001",
            portfolio_id="portfolio-001", 
            doc_name="Test Document.pdf"
        )
        
        assert document.doc_id == "doc-001"
        assert document.portfolio_id == "portfolio-001"
        assert document.doc_name == "Test Document.pdf"
    
    def test_guideline_creation(self):
        """Test Guideline entity creation."""
        guideline = Guideline(
            portfolio_id="portfolio-001",
            rule_id="rule-001",
            doc_id="doc-001",
            text="The fund shall maintain adequate liquidity."
        )
        
        assert guideline.portfolio_id == "portfolio-001"
        assert guideline.rule_id == "rule-001"
        assert guideline.text == "The fund shall maintain adequate liquidity."
    
    def test_guideline_provenance(self):
        """Test Guideline provenance generation."""
        guideline = Guideline(
            portfolio_id="portfolio-001",
            rule_id="rule-001", 
            doc_id="doc-001",
            text="Test guideline",
            part="III",
            section="A",
            subsection="1",
            page=25
        )
        
        provenance = guideline.full_provenance
        assert "Part III" in provenance
        assert "Section A" in provenance
        assert "Subsection 1" in provenance
        assert "Page 25" in provenance


class TestRepositories:
    """Test repository classes with mocked database."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        with patch('guidelines_agent.models.repositories.base_repository.db_manager') as mock:
            mock_cursor = MagicMock()
            mock.get_cursor.return_value.__enter__.return_value = mock_cursor
            yield mock_cursor
    
    def test_portfolio_repository_create(self, mock_db_manager):
        """Test PortfolioRepository create method."""
        repo = PortfolioRepository()
        portfolio = Portfolio(
            portfolio_id="test-001",
            portfolio_name="Test Portfolio"
        )
        
        mock_db_manager.rowcount = 1
        result = repo.create(portfolio)
        
        assert result is True
        mock_db_manager.execute.assert_called_once()
        
        # Check SQL and parameters
        call_args = mock_db_manager.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        
        assert "INSERT INTO portfolio" in sql
        assert params == (portfolio.portfolio_id, portfolio.portfolio_name)
    
    def test_portfolio_repository_get_by_id(self, mock_db_manager):
        """Test PortfolioRepository get_by_id method."""
        repo = PortfolioRepository()
        
        # Mock database response
        mock_db_manager.fetchall.return_value = [{
            'portfolio_id': 'test-001',
            'portfolio_name': 'Test Portfolio'
        }]
        
        portfolio = repo.get_by_id('test-001')
        
        assert portfolio is not None
        assert portfolio.portfolio_id == 'test-001'
        assert portfolio.portfolio_name == 'Test Portfolio'


class TestServices:
    """Test service layer classes."""
    
    @pytest.fixture
    def mock_repos(self):
        """Mock all repositories."""
        with patch('guidelines_agent.services.base_service.PortfolioRepository') as mock_portfolio_repo, \
             patch('guidelines_agent.services.base_service.DocumentRepository') as mock_doc_repo, \
             patch('guidelines_agent.services.base_service.GuidelineRepository') as mock_guideline_repo:
            
            yield {
                'portfolio': mock_portfolio_repo.return_value,
                'document': mock_doc_repo.return_value,
                'guideline': mock_guideline_repo.return_value
            }
    
    def test_guideline_service_create_portfolio_from_extraction(self, mock_repos):
        """Test GuidelineService portfolio creation from extraction."""
        from guidelines_agent.models.entities import ExtractionResult
        
        service = GuidelineService()
        
        extraction_result = ExtractionResult(
            is_valid=True,
            validation_summary="Valid document",
            portfolio_info={
                'portfolio_id': 'test-portfolio',
                'portfolio_name': 'Test Portfolio Fund'
            }
        )
        
        portfolio = service.create_portfolio_from_extraction(extraction_result)
        
        assert portfolio is not None
        assert portfolio.portfolio_id == 'test-portfolio'
        assert portfolio.portfolio_name == 'Test Portfolio Fund'
    
    def test_document_service_validation(self):
        """Test DocumentService validation methods."""
        from guidelines_agent.models.entities import ExtractionResult
        
        service = DocumentService()
        
        # Valid result
        valid_result = ExtractionResult(
            is_valid=True,
            validation_summary="Good document",
            guidelines=[{"text": "Test guideline"}],
            portfolio_info={"portfolio_id": "test"}
        )
        
        assert service.validate_extraction_result(valid_result) is True
        
        # Invalid result
        invalid_result = ExtractionResult(
            is_valid=False,
            validation_summary="Bad document"
        )
        
        assert service.validate_extraction_result(invalid_result) is False


@pytest.fixture(scope="session")
def test_server():
    """Start test server for integration tests."""
    # This would start a test instance of the server
    # For now, assumes server is already running
    yield "http://localhost:8000"


# Add performance benchmarks
class TestPerformance:
    """Performance and load testing."""
    
    @pytest.mark.performance
    def test_health_endpoint_performance(self, test_server):
        """Test health endpoint performance."""
        import requests
        import time
        
        times = []
        for _ in range(10):
            start = time.time()
            response = requests.get(f"{test_server}/health")
            end = time.time()
            
            assert response.status_code == 200
            times.append(end - start)
        
        avg_time = sum(times) / len(times)
        assert avg_time < 0.1, f"Health endpoint too slow: {avg_time:.3f}s average"
    
    @pytest.mark.performance
    def test_agent_query_performance(self, test_server):
        """Test agent query performance."""
        import requests
        import time
        
        payload = {"query": "What are investment restrictions?"}
        
        start = time.time()
        response = requests.post(
            f"{test_server}/agent/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        end = time.time()
        
        assert response.status_code == 200
        response_time = end - start
        assert response_time < 10.0, f"Agent query too slow: {response_time:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])