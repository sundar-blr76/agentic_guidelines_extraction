"""Agent-related API routes (/agent/*)."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from guidelines_agent.api.schemas.agent_schemas import (
    AgentQueryRequest, AgentQueryResponse,
    AgentChatRequest, AgentChatResponse,
    AgentInvokeRequest, AgentIngestionResponse,
    AgentStatsResponse
)
from guidelines_agent.api.schemas.common_schemas import ErrorResponse
from guidelines_agent.services import AgentService, SessionService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])

# Service instances
agent_service = AgentService()
session_service = SessionService()


@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(request: Request, query_request: AgentQueryRequest):
    """Process a natural language query about investment guidelines."""
    logger.info(f"Agent query: {query_request.query[:100]}...")
    
    try:
        result = agent_service.process_query(
            query=query_request.query,
            portfolio_ids=query_request.portfolio_ids,
            session_id=query_request.session_id
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return AgentQueryResponse(
            success=True,
            response=result['response'],
            session_id=result.get('session_id'),
            message="Query processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in agent query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(request: Request, chat_request: AgentChatRequest):
    """Chat with the agent using session-based conversation."""
    logger.info(f"Agent chat: {chat_request.message[:100]}...")
    
    try:
        # Create session if not provided
        session_id = chat_request.session_id
        if not session_id:
            session_result = session_service.create_session()
            if not session_result['success']:
                raise HTTPException(status_code=500, detail="Failed to create session")
            session_id = session_result['session_id']
        
        # Process the chat message
        result = agent_service.process_query(
            query=chat_request.message,
            session_id=session_id
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return AgentChatResponse(
            success=True,
            response=result['response'],
            session_id=session_id,
            message="Chat processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in agent chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoke", response_model=AgentIngestionResponse)
async def agent_invoke(request: Request, invoke_request: AgentInvokeRequest):
    """General agent invocation for various actions."""
    logger.info(f"Agent invoke: {invoke_request.action}")
    
    try:
        action = invoke_request.action.lower()
        params = invoke_request.parameters
        
        if action == "ingest":
            # Handle document ingestion
            pdf_path = params.get("pdf_path")
            if not pdf_path:
                raise HTTPException(status_code=400, detail="pdf_path required for ingest action")
            
            result = agent_service.process_document_ingestion(
                pdf_path=pdf_path,
                doc_name=params.get("doc_name")
            )
            
            if not result['success']:
                raise HTTPException(status_code=500, detail=result['error'])
            
            return AgentIngestionResponse(
                success=True,
                message=result['message'],
                doc_id=result.get('doc_id'),
                portfolio_id=result.get('portfolio_id'),
                guidelines_count=result.get('guidelines_count'),
                embeddings_generated=result.get('embeddings_generated'),
                validation_summary=result.get('validation_summary')
            )
        
        elif action == "stats":
            # Get system statistics
            result = agent_service.get_system_stats()
            
            if not result['success']:
                raise HTTPException(status_code=500, detail=result['error'])
            
            return AgentStatsResponse(
                success=True,
                stats=result['stats'],
                message="System statistics retrieved"
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent invoke: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=AgentIngestionResponse)
async def agent_ingest(request: Request, file: UploadFile = File(...)):
    """Ingest a PDF document by uploading the file."""
    logger.info(f"Agent ingest file: {file.filename}")
    
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        file_content = await file.read()
        
        # Process the file
        result = agent_service.process_file_upload_ingestion(file_content, file.filename)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return AgentIngestionResponse(
            success=True,
            message=result['message'],
            doc_id=result.get('doc_id'),
            portfolio_id=result.get('portfolio_id'),
            guidelines_count=result.get('guidelines_count'),
            embeddings_generated=result.get('embeddings_generated'),
            validation_summary=result.get('validation_summary')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent ingest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AgentStatsResponse)
async def get_agent_stats():
    """Get system statistics and status."""
    try:
        result = agent_service.get_system_stats()
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return AgentStatsResponse(
            success=True,
            stats=result['stats'],
            message="System statistics retrieved"
        )
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))