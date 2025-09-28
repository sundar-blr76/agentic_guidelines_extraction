"""Document repository for data access operations."""
from typing import List, Optional
from datetime import date
from guidelines_agent.models.entities.portfolio import Document
from guidelines_agent.models.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class DocumentRepository(BaseRepository):
    """Repository for document data access operations."""
    
    def create(self, document: Document) -> bool:
        """Create a new document."""
        try:
            command = """
                INSERT INTO document (doc_id, portfolio_id, doc_name, doc_date, human_readable_digest) 
                VALUES (%s, %s, %s, %s, %s)
            """
            affected_rows = self._execute_command(
                command, 
                (document.doc_id, document.portfolio_id, document.doc_name, 
                 document.doc_date, document.human_readable_digest)
            )
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error creating document {document.doc_id}: {e}")
            return False
    
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        query = """
            SELECT doc_id, portfolio_id, doc_name, doc_date, human_readable_digest 
            FROM document WHERE doc_id = %s
        """
        result = self._get_single_result(query, (doc_id,))
        
        if result:
            return Document(
                doc_id=result['doc_id'],
                portfolio_id=result['portfolio_id'],
                doc_name=result['doc_name'],
                doc_date=result['doc_date'],
                human_readable_digest=result['human_readable_digest']
            )
        return None
    
    def get_by_portfolio(self, portfolio_id: str) -> List[Document]:
        """Get all documents for a portfolio."""
        query = """
            SELECT doc_id, portfolio_id, doc_name, doc_date, human_readable_digest 
            FROM document WHERE portfolio_id = %s ORDER BY doc_date DESC, doc_name
        """
        results = self._execute_query(query, (portfolio_id,))
        
        return [
            Document(
                doc_id=row['doc_id'],
                portfolio_id=row['portfolio_id'],
                doc_name=row['doc_name'],
                doc_date=row['doc_date'],
                human_readable_digest=row['human_readable_digest']
            ) for row in results
        ]
    
    def exists(self, doc_id: str) -> bool:
        """Check if document exists."""
        return self._exists('document', {'doc_id': doc_id})
    
    def update(self, document: Document) -> bool:
        """Update existing document."""
        try:
            command = """
                UPDATE document SET doc_name = %s, doc_date = %s, human_readable_digest = %s 
                WHERE doc_id = %s
            """
            affected_rows = self._execute_command(
                command, 
                (document.doc_name, document.doc_date, document.human_readable_digest, document.doc_id)
            )
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error updating document {document.doc_id}: {e}")
            return False
    
    def delete(self, doc_id: str) -> bool:
        """Delete document by ID."""
        try:
            command = "DELETE FROM document WHERE doc_id = %s"
            affected_rows = self._execute_command(command, (doc_id,))
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def get_all(self) -> List[Document]:
        """Get all documents."""
        query = """
            SELECT doc_id, portfolio_id, doc_name, doc_date, human_readable_digest 
            FROM document ORDER BY doc_date DESC, doc_name
        """
        results = self._execute_query(query)
        
        return [
            Document(
                doc_id=row['doc_id'],
                portfolio_id=row['portfolio_id'],
                doc_name=row['doc_name'],
                doc_date=row['doc_date'],
                human_readable_digest=row['human_readable_digest']
            ) for row in results
        ]