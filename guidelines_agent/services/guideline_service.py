"""Guideline service for business logic related to guideline processing."""
from typing import List, Optional, Dict, Any
from guidelines_agent.services.base_service import BaseService
from guidelines_agent.models.entities import (
    Portfolio, Document, Guideline, GuidelineSearchResult, ExtractionResult
)
from guidelines_agent.core.embedding_service import generate_embeddings
import logging

logger = logging.getLogger(__name__)


class GuidelineService(BaseService):
    """Service for guideline processing and querying operations."""
    
    def create_portfolio_from_extraction(self, result: ExtractionResult) -> Optional[Portfolio]:
        """Create a Portfolio entity from extraction result."""
        if not result.portfolio_info:
            self.logger.error("No portfolio info in extraction result")
            return None
            
        portfolio_info = result.portfolio_info
        portfolio_id = portfolio_info.get('portfolio_id')
        portfolio_name = portfolio_info.get('portfolio_name')
        
        if not portfolio_id or not portfolio_name:
            self.logger.error("Missing portfolio_id or portfolio_name in extraction result")
            return None
            
        return Portfolio(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name
        )
    
    def create_guidelines_from_extraction(self, result: ExtractionResult, 
                                        doc_id: str) -> List[Guideline]:
        """Create Guideline entities from extraction result."""
        if not result.guidelines or not result.portfolio_info:
            return []
            
        portfolio_id = result.portfolio_info.get('portfolio_id')
        if not portfolio_id:
            self.logger.error("Missing portfolio_id in extraction result")
            return []
        
        guidelines = []
        for idx, guideline_data in enumerate(result.guidelines):
            try:
                # Generate rule_id if not present
                rule_id = guideline_data.get('rule_id')
                if not rule_id:
                    rule_id = f"rule_{idx+1:03d}"
                
                guideline = Guideline(
                    portfolio_id=portfolio_id,
                    rule_id=rule_id,
                    doc_id=doc_id,
                    text=guideline_data.get('text', ''),
                    part=guideline_data.get('part'),
                    section=guideline_data.get('section'),
                    subsection=guideline_data.get('subsection'),
                    page=guideline_data.get('page'),
                    provenance=guideline_data.get('provenance'),
                    structured_data=guideline_data.get('structured_data')
                )
                guidelines.append(guideline)
                
            except Exception as e:
                self.logger.warning(f"Error creating guideline {idx}: {e}")
                continue
                
        self.logger.info(f"Created {len(guidelines)} guidelines from extraction result")
        return guidelines
    
    def save_portfolio(self, portfolio: Portfolio) -> bool:
        """Save portfolio, handling existing portfolios."""
        try:
            # Check if portfolio already exists
            existing = self.portfolio_repo.get_by_id(portfolio.portfolio_id)
            if existing:
                # Update if name is different
                if existing.portfolio_name != portfolio.portfolio_name:
                    self.logger.info(f"Updating portfolio name: {existing.portfolio_name} -> {portfolio.portfolio_name}")
                    return self.portfolio_repo.update(portfolio)
                else:
                    self.logger.info(f"Portfolio {portfolio.portfolio_id} already exists with same name")
                    return True
            else:
                # Create new portfolio
                return self.portfolio_repo.create(portfolio)
                
        except Exception as e:
            self.logger.error(f"Error saving portfolio {portfolio.portfolio_id}: {e}")
            return False
    
    def save_guidelines_batch(self, guidelines: List[Guideline]) -> int:
        """Save multiple guidelines in batch."""
        if not guidelines:
            return 0
            
        try:
            return self.guideline_repo.create_batch(guidelines)
        except Exception as e:
            self.logger.error(f"Error saving guidelines batch: {e}")
            return 0
    
    def process_full_extraction(self, result: ExtractionResult, doc_name: str,
                              doc_id: Optional[str] = None) -> Dict[str, Any]:
        """Process complete extraction: save portfolio, document, and guidelines."""
        processing_result = {
            'success': False,
            'portfolio_saved': False,
            'document_saved': False,
            'guidelines_saved': 0,
            'errors': []
        }
        
        try:
            # 1. Create and save portfolio
            portfolio = self.create_portfolio_from_extraction(result)
            if not portfolio:
                processing_result['errors'].append("Failed to create portfolio from extraction")
                return processing_result
                
            portfolio_saved = self.save_portfolio(portfolio)
            processing_result['portfolio_saved'] = portfolio_saved
            
            if not portfolio_saved:
                processing_result['errors'].append("Failed to save portfolio")
                return processing_result
            
            # 2. Create and save document (requires document service)
            from guidelines_agent.services.document_service import DocumentService
            doc_service = DocumentService()
            
            document = doc_service.create_document_from_extraction(result, doc_name, doc_id)
            if not document:
                processing_result['errors'].append("Failed to create document from extraction")
                return processing_result
                
            document_saved = doc_service.save_document(document)
            processing_result['document_saved'] = document_saved
            
            if not document_saved:
                processing_result['errors'].append("Failed to save document")
                return processing_result
            
            # 3. Create and save guidelines
            guidelines = self.create_guidelines_from_extraction(result, document.doc_id)
            if not guidelines:
                processing_result['errors'].append("No guidelines created from extraction")
                return processing_result
                
            guidelines_saved = self.save_guidelines_batch(guidelines)
            processing_result['guidelines_saved'] = guidelines_saved
            
            if guidelines_saved == 0:
                processing_result['errors'].append("Failed to save any guidelines")
                return processing_result
            
            processing_result['success'] = True
            processing_result['doc_id'] = document.doc_id
            processing_result['portfolio_id'] = portfolio.portfolio_id
            
            self.logger.info(f"Successfully processed extraction: {guidelines_saved} guidelines saved")
            return processing_result
            
        except Exception as e:
            error_msg = f"Error processing extraction: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            processing_result['errors'].append(error_msg)
            return processing_result
    
    def search_guidelines(self, query_text: str, portfolio_ids: Optional[List[str]] = None,
                         top_k: int = 10, use_semantic: bool = True) -> List[GuidelineSearchResult]:
        """Search guidelines using text or semantic search."""
        if use_semantic:
            return self.semantic_search_guidelines(query_text, portfolio_ids, top_k)
        else:
            return self.text_search_guidelines(query_text, portfolio_ids, top_k)
    
    def text_search_guidelines(self, query_text: str, portfolio_ids: Optional[List[str]] = None,
                             top_k: int = 10) -> List[GuidelineSearchResult]:
        """Search guidelines using text matching."""
        try:
            guidelines = self.guideline_repo.search_by_text(query_text, portfolio_ids, top_k)
            
            search_results = []
            for rank, guideline in enumerate(guidelines, 1):
                portfolio_name = self.portfolio_repo.get_portfolio_name(guideline.portfolio_id)
                search_results.append(GuidelineSearchResult(
                    guideline=guideline,
                    rank=rank,
                    similarity=None,  # No similarity score for text search
                    portfolio_name=portfolio_name
                ))
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error in text search: {e}")
            return []
    
    def semantic_search_guidelines(self, query_text: str, portfolio_ids: Optional[List[str]] = None,
                                 top_k: int = 10, similarity_threshold: float = 0.5) -> List[GuidelineSearchResult]:
        """Search guidelines using semantic/vector search."""
        try:
            # Generate embedding for the query
            query_embedding = generate_embeddings([query_text])
            if not query_embedding or not query_embedding[0]:
                self.logger.error("Failed to generate query embedding")
                return []
            
            return self.guideline_repo.semantic_search(
                query_embedding[0], portfolio_ids, top_k, similarity_threshold
            )
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_guidelines_by_portfolio(self, portfolio_id: str, limit: Optional[int] = None) -> List[Guideline]:
        """Get all guidelines for a portfolio."""
        return self.guideline_repo.get_by_portfolio(portfolio_id, limit)
    
    def get_guideline_count_by_portfolio(self, portfolio_id: str) -> int:
        """Get count of guidelines for a portfolio."""
        return self.guideline_repo.count_by_portfolio(portfolio_id)
    
    def get_all_portfolios(self) -> List[Portfolio]:
        """Get all portfolios."""
        return self.portfolio_repo.get_all()
    
    def generate_missing_embeddings(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Generate embeddings for guidelines that don't have them."""
        try:
            guidelines = self.guideline_repo.get_guidelines_without_embeddings(limit)
            if not guidelines:
                return {'success': True, 'processed': 0, 'message': 'No guidelines need embeddings'}
            
            # Extract texts for batch embedding generation
            texts = [guideline.text for guideline in guidelines]
            embeddings = generate_embeddings(texts)
            
            if not embeddings or len(embeddings) != len(texts):
                return {'success': False, 'error': 'Failed to generate embeddings'}
            
            # Update guidelines with embeddings
            updated_count = 0
            for guideline, embedding in zip(guidelines, embeddings):
                if embedding and self.guideline_repo.update_embedding(
                    guideline.portfolio_id, guideline.rule_id, embedding
                ):
                    updated_count += 1
            
            return {
                'success': True,
                'processed': updated_count,
                'total_found': len(guidelines),
                'message': f'Updated embeddings for {updated_count} guidelines'
            }
            
        except Exception as e:
            error_msg = f"Error generating missing embeddings: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {'success': False, 'error': error_msg}