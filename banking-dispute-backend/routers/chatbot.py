# routes/chatbot.py - Chatbot API Router
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from services.mcp_service import MCPService
from services.session_service import SessionService

router = APIRouter(
    prefix="/api/chatbot",
    tags=["chatbot"]
)

# Initialize services
mcp_service = MCPService()
session_service = SessionService()

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: str
    context: Optional[Dict] = None

class ChatResponse(BaseModel):
    response: str
    type: str = "text"
    data: Optional[Dict] = None
    timestamp: datetime
    suggestions: Optional[List[str]] = None

class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[Dict]
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - processes user messages through MCP server
    
    Example:
    ```json
    {
        "message": "Calculate payment for $50000 at 8.5% for 5 years",
        "session_id": "user-123"
    }
    ```
    """
    try:
        # Store user message in session
        session_service.add_message(
            session_id=request.session_id,
            message=request.message,
            message_type="user"
        )
        
        # Process through MCP server
        response = mcp_service.process_query(
            message=request.message,
            session_id=request.session_id,
            context=request.context
        )
        
        # Store bot response in session
        session_service.add_message(
            session_id=request.session_id,
            message=response.response,
            message_type="bot",
            data=response.data
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/session/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    """
    Get conversation history for a specific session
    """
    try:
        history = session_service.get_session(session_id)
        if not history:
            raise HTTPException(status_code=404, detail="Session not found")
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")

@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear/delete a session and its history
    """
    try:
        success = session_service.clear_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session cleared successfully", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

@router.get("/sessions")
async def list_sessions():
    """
    List all active sessions
    """
    try:
        sessions = session_service.list_sessions()
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

@router.post("/feedback")
async def submit_feedback(
    session_id: str,
    message_id: str,
    rating: int,
    feedback: Optional[str] = None
):
    """
    Submit feedback for a specific message
    """
    try:
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        success = session_service.add_feedback(
            session_id=session_id,
            message_id=message_id,
            rating=rating,
            feedback=feedback
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Session or message not found")
        
        return {"message": "Feedback submitted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")