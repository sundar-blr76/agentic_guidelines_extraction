"""Session management API routes (/sessions/*)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from guidelines_agent.api.schemas.common_schemas import SuccessResponse, ErrorResponse
from guidelines_agent.services import SessionService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])

# Service instance
session_service = SessionService()


# --- Request/Response Schemas ---

class CreateSessionRequest(BaseModel):
    """Request schema for creating a session."""
    user_id: Optional[str] = Field(None, description="Optional user identifier")


class CreateSessionResponse(SuccessResponse):
    """Response schema for session creation."""
    session_id: str


class SessionInfoResponse(SuccessResponse):
    """Response schema for session information."""
    session: Dict[str, Any]


class SessionHistoryResponse(SuccessResponse):
    """Response schema for session history."""
    session_id: str
    interactions: list[Dict[str, Any]]


class UpdateSessionContextRequest(BaseModel):
    """Request schema for updating session context."""
    context_update: Dict[str, Any] = Field(..., description="Context updates")


class SessionStatsResponse(SuccessResponse):
    """Response schema for session statistics."""
    stats: Dict[str, Any]


# --- Route Handlers ---

@router.post("", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new user session."""
    logger.info("Creating new session")
    
    try:
        result = session_service.create_session(request.user_id)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return CreateSessionResponse(
            success=True,
            session_id=result['session_id'],
            message="Session created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(session_id: str):
    """Get session information and current context."""
    logger.info(f"Getting session info: {session_id}")
    
    try:
        result = session_service.get_session_info(session_id)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return SessionInfoResponse(
            success=True,
            session=result['session'],
            message="Session info retrieved"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str, limit: Optional[int] = None):
    """Get session conversation history."""
    logger.info(f"Getting session history: {session_id}")
    
    try:
        result = session_service.get_session_history(session_id, limit)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return SessionHistoryResponse(
            success=True,
            session_id=result['session_id'],
            interactions=result['interactions'],
            message="Session history retrieved"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{session_id}/context", response_model=SuccessResponse)
async def update_session_context(session_id: str, request: UpdateSessionContextRequest):
    """Update session context with new information."""
    logger.info(f"Updating session context: {session_id}")
    
    try:
        result = session_service.update_session_context(session_id, request.context_update)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return SuccessResponse(
            success=True,
            message=result['message'],
            data={"context": result['context']}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", response_model=SuccessResponse)
async def delete_session(session_id: str):
    """Delete a session."""
    logger.info(f"Deleting session: {session_id}")
    
    try:
        result = session_service.delete_session(session_id)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return SuccessResponse(
            success=True,
            message=result['message']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=SessionStatsResponse)
async def get_session_stats():
    """Get session statistics."""
    logger.info("Getting session statistics")
    
    try:
        result = session_service.get_active_sessions()
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return SessionStatsResponse(
            success=True,
            stats=result['stats'],
            message="Session statistics retrieved"
        )
        
    except Exception as e:
        logger.error(f"Error getting session stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))