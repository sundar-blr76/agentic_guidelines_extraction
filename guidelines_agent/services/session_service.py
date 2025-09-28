"""Session service for managing user sessions and context."""
import time
from typing import Dict, Any, Optional, List
from guidelines_agent.services.base_service import BaseService
from guidelines_agent.core.session_store import session_store, SessionInfo
import logging

logger = logging.getLogger(__name__)


class SessionService(BaseService):
    """Service for session management and context operations."""
    
    def create_session(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user session."""
        try:
            session_id = session_store.create_session(user_id)
            self.logger.info(f"Created new session: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "created": True
            }
            
        except Exception as e:
            error_msg = f"Error creating session: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session information and context."""
        try:
            session_info = session_store.get_session(session_id)
            if not session_info:
                return {
                    "success": False,
                    "error": f"Session {session_id} not found"
                }
            
            return {
                "success": True,
                "session": {
                    "session_id": session_id,
                    "created_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session_info.created_at)),
                    "last_accessed": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session_info.last_accessed)),
                    "context": session_info.context,
                    "conversation_history": session_store.get_conversation_history(session_id)
                }
            }
            
        except Exception as e:
            error_msg = f"Error getting session info: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_session_history(self, session_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get session conversation history."""
        try:
            session_info = session_store.get_session(session_id)
            if not session_info:
                return {
                    "success": False,
                    "error": f"Session {session_id} not found"
                }
            
            interactions = session_info.interactions
            if limit:
                interactions = interactions[-limit:]  # Get last N interactions
            
            return {
                "success": True,
                "session_id": session_id,
                "interactions": [
                    {
                        "timestamp": interaction.timestamp.isoformat(),
                        "query": interaction.query,
                        "response": interaction.response
                    } for interaction in interactions
                ]
            }
            
        except Exception as e:
            error_msg = f"Error getting session history: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def update_session_context(self, session_id: str, context_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update session context with new information."""
        try:
            session_info = session_store.get_session(session_id)
            if not session_info:
                return {
                    "success": False,
                    "error": f"Session {session_id} not found"
                }
            
            # Update context based on the provided data
            if 'portfolio_id' in context_update:
                session_info.context['current_portfolio'] = context_update['portfolio_id']
            
            if 'topic' in context_update:
                session_info.context['current_topic'] = context_update['topic']
            
            if 'preferences' in context_update:
                session_info.context.update(context_update['preferences'])
            
            # Update last activity
            session_info.update_activity()
            
            return {
                "success": True,
                "message": "Session context updated",
                "context": session_info.context
            }
            
        except Exception as e:
            error_msg = f"Error updating session context: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a session."""
        try:
            if session_store.delete_session(session_id):
                self.logger.info(f"Deleted session: {session_id}")
                return {
                    "success": True,
                    "message": f"Session {session_id} deleted"
                }
            else:
                return {
                    "success": False,
                    "error": f"Session {session_id} not found"
                }
                
        except Exception as e:
            error_msg = f"Error deleting session: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get all active sessions."""
        try:
            stats = session_store.get_session_stats()
            
            return {
                "success": True,
                "stats": {
                    "total_sessions": stats.get('total_sessions', 0),
                    "active_sessions": stats.get('active_sessions', 0),
                    "sessions_last_hour": stats.get('sessions_last_hour', 0)
                }
            }
            
        except Exception as e:
            error_msg = f"Error getting active sessions: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """Clean up expired sessions."""
        try:
            # This would need to be implemented in the session_store
            # For now, return a placeholder
            return {
                "success": True,
                "message": "Session cleanup not yet implemented",
                "cleaned_count": 0
            }
            
        except Exception as e:
            error_msg = f"Error cleaning up sessions: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }