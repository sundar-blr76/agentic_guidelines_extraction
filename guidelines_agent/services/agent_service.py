"""Agent service for AI agent orchestration and management."""
from typing import Dict, Any, Optional, List
from guidelines_agent.services.base_service import BaseService
from guidelines_agent.services.document_service import DocumentService
from guidelines_agent.services.guideline_service import GuidelineService
from guidelines_agent.core.session_store import session_store
import logging

logger = logging.getLogger(__name__)


class AgentService(BaseService):
    """Service for AI agent orchestration and high-level operations."""
    
    def __init__(self):
        super().__init__()
        self.document_service = DocumentService()
        self.guideline_service = GuidelineService()
        self._query_agent = None
        self._ingestion_agent = None
    
    def get_query_agent(self):
        """Get or create query agent."""
        if self._query_agent is None:
            from guidelines_agent.agent.agent_main import create_query_agent
            self._query_agent = create_query_agent()
        return self._query_agent
    
    def get_ingestion_agent(self):
        """Get or create ingestion agent.""" 
        if self._ingestion_agent is None:
            from guidelines_agent.agent.agent_main import create_ingestion_agent
            self._ingestion_agent = create_ingestion_agent()
        return self._ingestion_agent
    
    def get_stateful_query_agent(self, session_id: str):
        """Get or create stateful query agent for session."""
        from guidelines_agent.agent.agent_main import create_stateful_query_agent
        return create_stateful_query_agent(session_id)
    
    def process_query(self, query: str, portfolio_ids: Optional[List[str]] = None,
                     session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a user query using the appropriate agent."""
        try:
            if session_id:
                # Use stateful agent for session-based queries
                agent = self.get_stateful_query_agent(session_id)
                
                # Get session context for better prompting
                session_info = session_store.get_session(session_id)
                conversation_history = session_store.get_conversation_history(session_id) if session_info else ""
                session_context = f"Active session: {session_id}" if session_info else "No active context"
                
                response = agent.invoke({
                    "input": query,
                    "conversation_history": conversation_history,
                    "session_context": session_context
                })
                
                # Update session with the new interaction
                if session_info:
                    session_info.add_interaction(query, response.get("output", ""))
                
            else:
                # Use stateless agent for simple queries
                agent = self.get_query_agent()
                response = agent.invoke({"input": query})
            
            return {
                "success": True,
                "response": response.get("output", response),
                "session_id": session_id
            }
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "session_id": session_id
            }
    
    def process_document_ingestion(self, pdf_path: str, doc_name: Optional[str] = None) -> Dict[str, Any]:
        """Process document ingestion using the ingestion agent."""
        try:
            if not doc_name:
                import os
                doc_name = os.path.basename(pdf_path)
            
            # Step 1: Extract guidelines from PDF
            extraction_result = self.document_service.extract_guidelines_from_pdf(pdf_path)
            
            if not extraction_result.is_valid:
                return {
                    "success": False,
                    "error": "Document extraction failed",
                    "details": extraction_result.validation_summary
                }
            
            # Step 2: Process the full extraction (save portfolio, document, guidelines)
            processing_result = self.guideline_service.process_full_extraction(
                extraction_result, doc_name
            )
            
            if not processing_result['success']:
                return {
                    "success": False,
                    "error": "Failed to persist extracted data",
                    "details": processing_result['errors']
                }
            
            # Step 3: Generate embeddings for new guidelines
            embedding_result = self.guideline_service.generate_missing_embeddings()
            
            return {
                "success": True,
                "message": "Document ingestion completed successfully",
                "doc_id": processing_result['doc_id'],
                "portfolio_id": processing_result['portfolio_id'],
                "guidelines_count": processing_result['guidelines_saved'],
                "embeddings_generated": embedding_result.get('processed', 0),
                "validation_summary": extraction_result.validation_summary
            }
            
        except Exception as e:
            error_msg = f"Error processing document ingestion: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def process_file_upload_ingestion(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process document ingestion from uploaded file content."""
        import tempfile
        import os
        
        # Save uploaded content to temporary file
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Process the temporary file
            result = self.process_document_ingestion(temp_file_path, filename)
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing file upload: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
    
    def get_portfolio_summary(self, portfolio_id: str) -> Dict[str, Any]:
        """Get summary information for a portfolio."""
        try:
            portfolio = self.portfolio_repo.get_by_id(portfolio_id)
            if not portfolio:
                return {
                    "success": False,
                    "error": f"Portfolio {portfolio_id} not found"
                }
            
            guidelines_count = self.guideline_service.get_guideline_count_by_portfolio(portfolio_id)
            documents = self.document_service.get_documents_by_portfolio(portfolio_id)
            
            return {
                "success": True,
                "portfolio": {
                    "portfolio_id": portfolio.portfolio_id,
                    "portfolio_name": portfolio.portfolio_name,
                    "guidelines_count": guidelines_count,
                    "documents_count": len(documents),
                    "documents": [
                        {
                            "doc_id": doc.doc_id,
                            "doc_name": doc.doc_name,
                            "doc_date": doc.doc_date.isoformat() if doc.doc_date else None
                        } for doc in documents
                    ]
                }
            }
            
        except Exception as e:
            error_msg = f"Error getting portfolio summary: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        try:
            portfolios = self.guideline_service.get_all_portfolios()
            total_guidelines = sum(
                self.guideline_service.get_guideline_count_by_portfolio(p.portfolio_id) 
                for p in portfolios
            )
            
            # Get guidelines without embeddings
            guidelines_without_embeddings = self.guideline_repo.get_guidelines_without_embeddings(limit=1)
            needs_embeddings = len(guidelines_without_embeddings) > 0
            
            return {
                "success": True,
                "stats": {
                    "total_portfolios": len(portfolios),
                    "total_guidelines": total_guidelines,
                    "needs_embeddings": needs_embeddings,
                    "portfolios": [
                        {
                            "portfolio_id": p.portfolio_id,
                            "portfolio_name": p.portfolio_name,
                            "guidelines_count": self.guideline_service.get_guideline_count_by_portfolio(p.portfolio_id)
                        } for p in portfolios
                    ]
                }
            }
            
        except Exception as e:
            error_msg = f"Error getting system stats: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }