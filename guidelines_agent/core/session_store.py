"""
Simple server-side session management for stateful conversations.
Uses in-memory storage with LangChain memory classes for conversation history.
"""
import uuid
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from langchain.memory import ConversationBufferWindowMemory
import logging

logger = logging.getLogger(__name__)

@dataclass
class SessionInfo:
    session_id: str
    created_at: float
    last_accessed: float
    memory: ConversationBufferWindowMemory
    context: Dict[str, Any]  # Store additional context like active portfolios, preferences

class SessionStore:
    """
    Simple in-memory session store with conversation memory.
    """
    
    def __init__(self, session_timeout: int = 3600, max_sessions: int = 100):
        """
        Args:
            session_timeout: Session timeout in seconds (default 1 hour)
            max_sessions: Maximum number of concurrent sessions
        """
        self._sessions: Dict[str, SessionInfo] = {}
        self._session_timeout = session_timeout
        self._max_sessions = max_sessions
        
    def create_session(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Create a new session and return session_id."""
        # Clean up expired sessions first
        self._cleanup_expired_sessions()
        
        # If at max capacity, remove oldest session
        if len(self._sessions) >= self._max_sessions:
            self._remove_oldest_session()
        
        session_id = str(uuid.uuid4())
        current_time = time.time()
        
        # Create memory with window of last 10 exchanges (20 messages)
        memory = ConversationBufferWindowMemory(
            k=20,  # Keep last 20 messages (10 exchanges)
            memory_key="chat_history",
            return_messages=True
        )
        
        session_info = SessionInfo(
            session_id=session_id,
            created_at=current_time,
            last_accessed=current_time,
            memory=memory,
            context=context or {}
        )
        
        self._sessions[session_id] = session_info
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session info, updating last accessed time."""
        if session_id not in self._sessions:
            return None
            
        session = self._sessions[session_id]
        
        # Check if session has expired
        if time.time() - session.last_accessed > self._session_timeout:
            del self._sessions[session_id]
            logger.info(f"Session expired and removed: {session_id}")
            return None
        
        # Update last accessed time
        session.last_accessed = time.time()
        return session
    
    def add_message(self, session_id: str, user_message: str, ai_message: str) -> bool:
        """Add a user/AI message pair to session memory."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Add to memory
        session.memory.save_context(
            {"input": user_message}, 
            {"output": ai_message}
        )
        
        logger.debug(f"Added message to session {session_id}")
        return True
    
    def get_conversation_history(self, session_id: str) -> str:
        """Get formatted conversation history for prompt inclusion."""
        session = self.get_session(session_id)
        if not session:
            return ""
        
        # Get the memory variables
        memory_vars = session.memory.load_memory_variables({})
        history = memory_vars.get("chat_history", [])
        
        if not history:
            return ""
        
        # Format as text for prompt
        formatted_history = []
        for message in history:
            if hasattr(message, 'type') and hasattr(message, 'content'):
                role = "User" if message.type == "human" else "Assistant"
                formatted_history.append(f"{role}: {message.content}")
        
        return "\n".join(formatted_history)
    
    def update_context(self, session_id: str, context_update: Dict[str, Any]) -> bool:
        """Update session context (active portfolios, preferences, etc.)."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.context.update(context_update)
        logger.debug(f"Updated context for session {session_id}: {context_update}")
        return True
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context."""
        session = self.get_session(session_id)
        return session.context if session else {}
    
    def delete_session(self, session_id: str) -> bool:
        """Explicitly delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current sessions."""
        current_time = time.time()
        active_sessions = 0
        
        for session in self._sessions.values():
            if current_time - session.last_accessed <= self._session_timeout:
                active_sessions += 1
        
        return {
            "total_sessions": len(self._sessions),
            "active_sessions": active_sessions,
            "max_sessions": self._max_sessions,
            "session_timeout": self._session_timeout
        }
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self._sessions.items():
            if current_time - session.last_accessed > self._session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
    
    def _remove_oldest_session(self):
        """Remove the oldest session when at capacity."""
        if not self._sessions:
            return
        
        oldest_session_id = min(self._sessions.keys(), 
                               key=lambda sid: self._sessions[sid].last_accessed)
        del self._sessions[oldest_session_id]
        logger.info(f"Removed oldest session due to capacity: {oldest_session_id}")

# Global session store instance
session_store = SessionStore()