"""Guideline repository for data access operations."""
from typing import List, Optional, Dict, Any
from guidelines_agent.models.entities.portfolio import Guideline, GuidelineSearchResult
from guidelines_agent.models.repositories.base_repository import BaseRepository
import logging
import json

logger = logging.getLogger(__name__)


class GuidelineRepository(BaseRepository):
    """Repository for guideline data access operations."""
    
    def create(self, guideline: Guideline) -> bool:
        """Create a new guideline."""
        try:
            command = """
                INSERT INTO guideline (portfolio_id, rule_id, doc_id, part, section, subsection, 
                                     text, page, provenance, structured_data, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Convert structured_data to JSON if present
            structured_json = json.dumps(guideline.structured_data) if guideline.structured_data else None
            
            affected_rows = self._execute_command(
                command,
                (guideline.portfolio_id, guideline.rule_id, guideline.doc_id,
                 guideline.part, guideline.section, guideline.subsection,
                 guideline.text, guideline.page, guideline.provenance,
                 structured_json, guideline.embedding)
            )
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error creating guideline {guideline.rule_id}: {e}")
            return False
    
    def create_batch(self, guidelines: List[Guideline]) -> int:
        """Create multiple guidelines in batch."""
        if not guidelines:
            return 0
            
        try:
            command = """
                INSERT INTO guideline (portfolio_id, rule_id, doc_id, part, section, subsection, 
                                     text, page, provenance, structured_data, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = []
            for guideline in guidelines:
                structured_json = json.dumps(guideline.structured_data) if guideline.structured_data else None
                params.append((
                    guideline.portfolio_id, guideline.rule_id, guideline.doc_id,
                    guideline.part, guideline.section, guideline.subsection,
                    guideline.text, guideline.page, guideline.provenance,
                    structured_json, guideline.embedding
                ))
            
            return self._execute_batch(command, params)
        except Exception as e:
            logger.error(f"Error creating guidelines batch: {e}")
            return 0
    
    def get_by_id(self, portfolio_id: str, rule_id: str) -> Optional[Guideline]:
        """Get guideline by portfolio ID and rule ID."""
        query = """
            SELECT portfolio_id, rule_id, doc_id, part, section, subsection,
                   text, page, provenance, structured_data, embedding
            FROM guideline WHERE portfolio_id = %s AND rule_id = %s
        """
        result = self._get_single_result(query, (portfolio_id, rule_id))
        
        if result:
            return self._row_to_guideline(result)
        return None
    
    def get_by_portfolio(self, portfolio_id: str, limit: Optional[int] = None) -> List[Guideline]:
        """Get all guidelines for a portfolio."""
        query = """
            SELECT portfolio_id, rule_id, doc_id, part, section, subsection,
                   text, page, provenance, structured_data, embedding
            FROM guideline WHERE portfolio_id = %s
            ORDER BY rule_id
        """
        if limit:
            query += f" LIMIT {limit}"
            
        results = self._execute_query(query, (portfolio_id,))
        return [self._row_to_guideline(row) for row in results]
    
    def get_by_document(self, doc_id: str) -> List[Guideline]:
        """Get all guidelines for a document."""
        query = """
            SELECT portfolio_id, rule_id, doc_id, part, section, subsection,
                   text, page, provenance, structured_data, embedding
            FROM guideline WHERE doc_id = %s
            ORDER BY rule_id
        """
        results = self._execute_query(query, (doc_id,))
        return [self._row_to_guideline(row) for row in results]
    
    def search_by_text(self, search_text: str, portfolio_ids: Optional[List[str]] = None, 
                       limit: int = 10) -> List[Guideline]:
        """Search guidelines by text content."""
        query = """
            SELECT portfolio_id, rule_id, doc_id, part, section, subsection,
                   text, page, provenance, structured_data, embedding
            FROM guideline 
            WHERE text ILIKE %s
        """
        params = [f"%{search_text}%"]
        
        if portfolio_ids:
            placeholders = ",".join(["%s"] * len(portfolio_ids))
            query += f" AND portfolio_id IN ({placeholders})"
            params.extend(portfolio_ids)
        
        query += f" ORDER BY portfolio_id, rule_id LIMIT {limit}"
        
        results = self._execute_query(query, params)
        return [self._row_to_guideline(row) for row in results]
    
    def semantic_search(self, query_embedding: List[float], portfolio_ids: Optional[List[str]] = None,
                       top_k: int = 10, similarity_threshold: float = 0.5) -> List[GuidelineSearchResult]:
        """Perform semantic search using vector similarity."""
        query_base = """
            SELECT g.portfolio_id, g.rule_id, g.doc_id, g.part, g.section, g.subsection,
                   g.text, g.page, g.provenance, g.structured_data, g.embedding,
                   p.portfolio_name,
                   (1 - (g.embedding <=> %s::vector)) as similarity
            FROM guideline g
            JOIN portfolio p ON g.portfolio_id = p.portfolio_id
            WHERE g.embedding IS NOT NULL
              AND (1 - (g.embedding <=> %s::vector)) >= %s
        """
        
        params = [query_embedding, query_embedding, similarity_threshold]
        
        if portfolio_ids:
            placeholders = ",".join(["%s"] * len(portfolio_ids))
            query_base += f" AND g.portfolio_id IN ({placeholders})"
            params.extend(portfolio_ids)
        
        query_base += f" ORDER BY similarity DESC LIMIT {top_k}"
        
        try:
            results = self._execute_query(query_base, params)
            
            search_results = []
            for rank, row in enumerate(results, 1):
                guideline = self._row_to_guideline(row)
                search_results.append(GuidelineSearchResult(
                    guideline=guideline,
                    rank=rank,
                    similarity=float(row['similarity']),
                    portfolio_name=row['portfolio_name']
                ))
            
            return search_results
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def update_embedding(self, portfolio_id: str, rule_id: str, embedding: List[float]) -> bool:
        """Update embedding for a specific guideline."""
        try:
            command = "UPDATE guideline SET embedding = %s WHERE portfolio_id = %s AND rule_id = %s"
            affected_rows = self._execute_command(command, (embedding, portfolio_id, rule_id))
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error updating embedding for {portfolio_id}/{rule_id}: {e}")
            return False
    
    def get_guidelines_without_embeddings(self, limit: Optional[int] = None) -> List[Guideline]:
        """Get guidelines that don't have embeddings yet."""
        query = """
            SELECT portfolio_id, rule_id, doc_id, part, section, subsection,
                   text, page, provenance, structured_data, embedding
            FROM guideline 
            WHERE embedding IS NULL
            ORDER BY portfolio_id, rule_id
        """
        if limit:
            query += f" LIMIT {limit}"
            
        results = self._execute_query(query)
        return [self._row_to_guideline(row) for row in results]
    
    def count_by_portfolio(self, portfolio_id: str) -> int:
        """Count guidelines for a portfolio."""
        query = "SELECT COUNT(*) as count FROM guideline WHERE portfolio_id = %s"
        result = self._get_single_result(query, (portfolio_id,))
        return result['count'] if result else 0
    
    def exists(self, portfolio_id: str, rule_id: str) -> bool:
        """Check if guideline exists."""
        return self._exists('guideline', {'portfolio_id': portfolio_id, 'rule_id': rule_id})
    
    def update(self, guideline: Guideline) -> bool:
        """Update existing guideline."""
        try:
            command = """
                UPDATE guideline SET doc_id = %s, part = %s, section = %s, subsection = %s,
                                   text = %s, page = %s, provenance = %s, structured_data = %s, embedding = %s
                WHERE portfolio_id = %s AND rule_id = %s
            """
            structured_json = json.dumps(guideline.structured_data) if guideline.structured_data else None
            
            affected_rows = self._execute_command(
                command,
                (guideline.doc_id, guideline.part, guideline.section, guideline.subsection,
                 guideline.text, guideline.page, guideline.provenance, structured_json,
                 guideline.embedding, guideline.portfolio_id, guideline.rule_id)
            )
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error updating guideline {guideline.portfolio_id}/{guideline.rule_id}: {e}")
            return False
    
    def delete(self, portfolio_id: str, rule_id: str) -> bool:
        """Delete guideline by portfolio ID and rule ID."""
        try:
            command = "DELETE FROM guideline WHERE portfolio_id = %s AND rule_id = %s"
            affected_rows = self._execute_command(command, (portfolio_id, rule_id))
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error deleting guideline {portfolio_id}/{rule_id}: {e}")
            return False
    
    def delete_by_portfolio(self, portfolio_id: str) -> int:
        """Delete all guidelines for a portfolio."""
        try:
            command = "DELETE FROM guideline WHERE portfolio_id = %s"
            return self._execute_command(command, (portfolio_id,))
        except Exception as e:
            logger.error(f"Error deleting guidelines for portfolio {portfolio_id}: {e}")
            return 0
    
    def delete_by_document(self, doc_id: str) -> int:
        """Delete all guidelines for a document."""
        try:
            command = "DELETE FROM guideline WHERE doc_id = %s"
            return self._execute_command(command, (doc_id,))
        except Exception as e:
            logger.error(f"Error deleting guidelines for document {doc_id}: {e}")
            return 0
    
    def _row_to_guideline(self, row: Dict[str, Any]) -> Guideline:
        """Convert database row to Guideline entity."""
        structured_data = None
        if row['structured_data']:
            try:
                # Check if it's already a dict/object
                if isinstance(row['structured_data'], (dict, list)):
                    structured_data = row['structured_data']
                else:
                    # Try to parse as JSON string
                    structured_data = json.loads(row['structured_data'])
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid JSON in structured_data for {row['portfolio_id']}/{row['rule_id']}")
                structured_data = None
        
        return Guideline(
            portfolio_id=row['portfolio_id'],
            rule_id=row['rule_id'],
            doc_id=row['doc_id'],
            text=row['text'],
            part=row['part'],
            section=row['section'],
            subsection=row['subsection'],
            page=row['page'],
            provenance=row['provenance'],
            structured_data=structured_data,
            embedding=row['embedding']
        )
    
    def delete_by_portfolio(self, portfolio_id: str) -> int:
        """Delete all guidelines for a specific portfolio."""
        try:
            command = "DELETE FROM guideline WHERE portfolio_id = %s"
            deleted_count = self._execute_command(command, (portfolio_id,))
            logger.info(f"Deleted {deleted_count} guidelines for portfolio {portfolio_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting guidelines for portfolio {portfolio_id}: {e}")
            return 0