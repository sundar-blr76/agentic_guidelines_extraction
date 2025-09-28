"""Base repository class with common database operations."""
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict
from guidelines_agent.models.database import db_manager
import logging

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Base repository class providing common database operations."""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def _execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def _execute_command(self, command: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE command and return affected rows."""
        with self.db_manager.get_cursor() as cursor:
            cursor.execute(command, params)
            return cursor.rowcount
    
    def _execute_batch(self, command: str, param_list: List[tuple]) -> int:
        """Execute a batch of commands."""
        with self.db_manager.get_cursor() as cursor:
            cursor.executemany(command, param_list)
            return cursor.rowcount
    
    def _get_single_result(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute query and return single result or None."""
        results = self._execute_query(query, params)
        return results[0] if results else None
    
    def _exists(self, table: str, conditions: Dict[str, Any]) -> bool:
        """Check if record exists with given conditions."""
        where_clause = " AND ".join(f"{key} = %s" for key in conditions.keys())
        query = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
        params = tuple(conditions.values())
        return bool(self._get_single_result(query, params))
    
    @abstractmethod
    def create(self, entity: Any) -> bool:
        """Create a new entity."""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[Any]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    def update(self, entity: Any) -> bool:
        """Update existing entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        pass