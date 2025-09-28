"""Database connection and configuration management."""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
from typing import Optional, Generator, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str
    port: str
    dbname: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables or defaults."""
        # Import here to avoid circular imports
        from guidelines_agent.core.config import DB_CONFIG
        return cls(**DB_CONFIG)


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        
    def get_connection(self):
        """Get a direct database connection."""
        try:
            return psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                dbname=self.config.dbname,
                user=self.config.user,
                password=self.config.password,
                cursor_factory=RealDictCursor
            )
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    @contextmanager
    def get_db_session(self) -> Generator[Any, None, None]:
        """Context manager for database transactions."""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self) -> Generator[Any, None, None]:
        """Context manager for database cursor operations."""
        with self.get_db_session() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()


# Global database manager instance
db_manager = DatabaseManager()