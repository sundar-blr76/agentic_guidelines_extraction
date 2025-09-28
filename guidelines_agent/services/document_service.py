"""Document service for business logic related to document processing."""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from guidelines_agent.services.base_service import BaseService
from guidelines_agent.models.entities import Document, ExtractionResult
from guidelines_agent.core.extract import extract_guidelines_from_pdf
import logging

logger = logging.getLogger(__name__)


class DocumentService(BaseService):
    """Service for document processing and extraction operations."""
    
    def extract_guidelines_from_pdf(self, pdf_path: str) -> ExtractionResult:
        """Extract guidelines from a PDF file and return structured result."""
        self.logger.info(f"Starting guideline extraction from: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            self.logger.error(error_msg)
            return ExtractionResult(
                is_valid=False,
                validation_summary=error_msg,
                error_message=error_msg
            )
        
        try:
            # Call the existing extraction logic
            result = extract_guidelines_from_pdf(pdf_path)
            
            # Convert to our ExtractionResult format
            if isinstance(result, dict):
                # Build portfolio_info from individual fields if not present
                portfolio_info = result.get('portfolio_info', {})
                if not portfolio_info:
                    # Extract portfolio info from individual fields
                    portfolio_info = {
                        'portfolio_id': result.get('portfolio_id'),
                        'portfolio_name': result.get('portfolio_name'),
                        'doc_id': result.get('doc_id'),
                        'doc_name': result.get('doc_name'),
                        'doc_date': result.get('doc_date')
                    }
                    # Remove None values
                    portfolio_info = {k: v for k, v in portfolio_info.items() if v is not None}
                    
                return ExtractionResult(
                    is_valid=result.get('is_valid_document', False),
                    validation_summary=result.get('validation_summary', 'No validation summary'),
                    guidelines=result.get('guidelines', []),
                    portfolio_info=portfolio_info,
                    error_message=result.get('error_message')
                )
            else:
                # Handle old format (list of guidelines, text)
                if isinstance(result, tuple) and len(result) == 2:
                    guidelines_list, guidelines_text = result
                    return ExtractionResult(
                        is_valid=True,
                        validation_summary="Document processed successfully",
                        guidelines=guidelines_list,
                        portfolio_info={}
                    )
                else:
                    raise ValueError("Unexpected result format from extraction")
                    
        except Exception as e:
            error_msg = f"Error extracting guidelines: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ExtractionResult(
                is_valid=False,
                validation_summary=error_msg,
                error_message=error_msg
            )
    
    def validate_extraction_result(self, result: ExtractionResult) -> bool:
        """Validate that extraction result contains required data."""
        if not result.is_valid:
            return False
            
        if not result.guidelines:
            self.logger.warning("Extraction result contains no guidelines")
            return False
            
        if not result.portfolio_info:
            self.logger.warning("Extraction result missing portfolio information")
            return False
            
        return True
    
    def create_document_from_extraction(self, result: ExtractionResult, 
                                      doc_name: str, doc_id: Optional[str] = None) -> Optional[Document]:
        """Create a Document entity from extraction result."""
        if not self.validate_extraction_result(result):
            return None
            
        portfolio_info = result.portfolio_info
        if not portfolio_info or 'portfolio_id' not in portfolio_info:
            self.logger.error("Missing portfolio_id in extraction result")
            return None
        
        # Generate doc_id if not provided
        if not doc_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_name = "".join(c for c in doc_name if c.isalnum() or c in "._-")[:50]
            doc_id = f"doc_{clean_name}_{timestamp}"
        
        # Create human readable digest
        digest_lines = [
            f"Document: {doc_name}",
            f"Portfolio: {portfolio_info.get('portfolio_name', 'Unknown')}",
            f"Guidelines extracted: {len(result.guidelines)}",
            f"Extraction date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        if result.validation_summary:
            digest_lines.append(f"Validation: {result.validation_summary}")
        
        document = Document(
            doc_id=doc_id,
            portfolio_id=portfolio_info['portfolio_id'],
            doc_name=doc_name,
            doc_date=datetime.now().date(),
            human_readable_digest="\n".join(digest_lines)
        )
        
        return document
    
    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self.document_repo.get_by_id(doc_id)
    
    def get_documents_by_portfolio(self, portfolio_id: str) -> list[Document]:
        """Get all documents for a portfolio."""
        return self.document_repo.get_by_portfolio(portfolio_id)
    
    def save_document(self, document: Document) -> bool:
        """Save document to repository."""
        try:
            return self.document_repo.create(document)
        except Exception as e:
            self.logger.error(f"Error saving document {document.doc_id}: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete document and associated guidelines."""
        try:
            # First delete associated guidelines
            deleted_guidelines = self.guideline_repo.delete_by_document(doc_id)
            self.logger.info(f"Deleted {deleted_guidelines} guidelines for document {doc_id}")
            
            # Then delete the document
            success = self.document_repo.delete(doc_id)
            if success:
                self.logger.info(f"Successfully deleted document {doc_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id}: {e}")
            return False