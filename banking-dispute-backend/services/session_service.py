# services/session_service.py - Session Management Service
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict

class SessionService:
    """Service for managing user sessions and conversation history"""
    
    def __init__(self):
        # In-memory storage (use Redis or database in production)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.feedback: Dict[str, List[Dict]] = defaultdict(list)
    
    def create_session(self, session_id: str) -> Dict:
        """Create a new session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "messages": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "metadata": {}
            }
        return self.sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def add_message(
        self,
        session_id: str,
        message: str,
        message_type: str = "user",
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Add a message to session
        
        Args:
            session_id: Session identifier
            message: Message content
            message_type: Type of message (user/bot)
            data: Additional data attached to message
        
        Returns:
            The created message object
        """
        # Create session if it doesn't exist
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        message_obj = {
            "id": f"{session_id}_{len(self.sessions[session_id]['messages'])}",
            "message": message,
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        self.sessions[session_id]["messages"].append(message_obj)
        self.sessions[session_id]["updated_at"] = datetime.now()
        
        return message_obj
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
        
        Returns:
            List of messages
        """
        if session_id not in self.sessions:
            return []
        
        messages = self.sessions[session_id]["messages"]
        
        if limit:
            return messages[-limit:]
        return messages
    
    def update_session_metadata(
        self,
        session_id: str,
        metadata: Dict
    ) -> bool:
        """
        Update session metadata
        
        Args:
            session_id: Session identifier
            metadata: Metadata to update
        
        Returns:
            Success status
        """
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["metadata"].update(metadata)
        self.sessions[session_id]["updated_at"] = datetime.now()
        
        return True
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear/delete a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Success status
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[Dict]:
        """
        List all active sessions
        
        Returns:
            List of session summaries
        """
        summaries = []
        for session_id, session in self.sessions.items():
            summaries.append({
                "session_id": session_id,
                "message_count": len(session["messages"]),
                "created_at": session["created_at"].isoformat(),
                "updated_at": session["updated_at"].isoformat(),
                "last_message": session["messages"][-1]["message"] if session["messages"] else None
            })
        return summaries
    
    def add_feedback(
        self,
        session_id: str,
        message_id: str,
        rating: int,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Add feedback for a message
        
        Args:
            session_id: Session identifier
            message_id: Message identifier
            rating: Rating (1-5)
            feedback: Optional feedback text
        
        Returns:
            Success status
        """
        if session_id not in self.sessions:
            return False
        
        # Find the message
        message_found = False
        for msg in self.sessions[session_id]["messages"]:
            if msg["id"] == message_id:
                message_found = True
                break
        
        if not message_found:
            return False
        
        feedback_obj = {
            "session_id": session_id,
            "message_id": message_id,
            "rating": rating,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedback[session_id].append(feedback_obj)
        
        return True
    
    def get_session_feedback(self, session_id: str) -> List[Dict]:
        """
        Get all feedback for a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of feedback objects
        """
        return self.feedback.get(session_id, [])
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """
        Get statistics for a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary with session statistics
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        messages = session["messages"]
        
        user_messages = [m for m in messages if m["type"] == "user"]
        bot_messages = [m for m in messages if m["type"] == "bot"]
        
        # Calculate session duration
        if messages:
            first_msg_time = datetime.fromisoformat(messages[0]["timestamp"])
            last_msg_time = datetime.fromisoformat(messages[-1]["timestamp"])
            duration_seconds = (last_msg_time - first_msg_time).total_seconds()
        else:
            duration_seconds = 0
        
        # Get average rating from feedback
        session_feedback = self.feedback.get(session_id, [])
        avg_rating = sum(f["rating"] for f in session_feedback) / len(session_feedback) if session_feedback else None
        
        return {
            "session_id": session_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "bot_messages": len(bot_messages),
            "duration_seconds": int(duration_seconds),
            "duration_minutes": round(duration_seconds / 60, 2),
            "created_at": session["created_at"].isoformat(),
            "updated_at": session["updated_at"].isoformat(),
            "average_rating": avg_rating,
            "feedback_count": len(session_feedback)
        }
    
    def search_sessions(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search sessions by message content
        
        Args:
            query: Search query
            limit: Maximum results to return
        
        Returns:
            List of matching sessions
        """
        results = []
        query_lower = query.lower()
        
        for session_id, session in self.sessions.items():
            for message in session["messages"]:
                if query_lower in message["message"].lower():
                    results.append({
                        "session_id": session_id,
                        "message": message["message"],
                        "timestamp": message["timestamp"],
                        "type": message["type"]
                    })
                    break  # Only include each session once
            
            if len(results) >= limit:
                break
        
        return results
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Clean up sessions older than specified days
        
        Args:
            days: Number of days to keep sessions
        
        Returns:
            Number of sessions deleted
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        sessions_to_delete = []
        
        for session_id, session in self.sessions.items():
            if session["updated_at"].timestamp() < cutoff_date:
                sessions_to_delete.append(session_id)
        
        for session_id in sessions_to_delete:
            del self.sessions[session_id]
            if session_id in self.feedback:
                del self.feedback[session_id]
        
        return len(sessions_to_delete)