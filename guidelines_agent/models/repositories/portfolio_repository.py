"""Portfolio repository for data access operations."""
from typing import List, Optional
from guidelines_agent.models.entities.portfolio import Portfolio
from guidelines_agent.models.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class PortfolioRepository(BaseRepository):
    """Repository for portfolio data access operations."""
    
    def create(self, portfolio: Portfolio) -> bool:
        """Create a new portfolio."""
        try:
            command = "INSERT INTO portfolio (portfolio_id, portfolio_name) VALUES (%s, %s)"
            affected_rows = self._execute_command(command, (portfolio.portfolio_id, portfolio.portfolio_name))
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error creating portfolio {portfolio.portfolio_id}: {e}")
            return False
    
    def get_by_id(self, portfolio_id: str) -> Optional[Portfolio]:
        """Get portfolio by ID."""
        query = "SELECT portfolio_id, portfolio_name FROM portfolio WHERE portfolio_id = %s"
        result = self._get_single_result(query, (portfolio_id,))
        
        if result:
            return Portfolio(
                portfolio_id=result['portfolio_id'],
                portfolio_name=result['portfolio_name']
            )
        return None
    
    def get_all(self) -> List[Portfolio]:
        """Get all portfolios."""
        query = "SELECT portfolio_id, portfolio_name FROM portfolio ORDER BY portfolio_name"
        results = self._execute_query(query)
        
        return [
            Portfolio(
                portfolio_id=row['portfolio_id'],
                portfolio_name=row['portfolio_name']
            ) for row in results
        ]
    
    def exists(self, portfolio_id: str) -> bool:
        """Check if portfolio exists."""
        return self._exists('portfolio', {'portfolio_id': portfolio_id})
    
    def update(self, portfolio: Portfolio) -> bool:
        """Update existing portfolio."""
        try:
            command = "UPDATE portfolio SET portfolio_name = %s WHERE portfolio_id = %s"
            affected_rows = self._execute_command(command, (portfolio.portfolio_name, portfolio.portfolio_id))
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error updating portfolio {portfolio.portfolio_id}: {e}")
            return False
    
    def delete(self, portfolio_id: str) -> bool:
        """Delete portfolio by ID."""
        try:
            command = "DELETE FROM portfolio WHERE portfolio_id = %s"
            affected_rows = self._execute_command(command, (portfolio_id,))
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error deleting portfolio {portfolio_id}: {e}")
            return False
    
    def get_portfolio_name(self, portfolio_id: str) -> Optional[str]:
        """Get just the portfolio name by ID."""
        query = "SELECT portfolio_name FROM portfolio WHERE portfolio_id = %s"
        result = self._get_single_result(query, (portfolio_id,))
        return result['portfolio_name'] if result else None