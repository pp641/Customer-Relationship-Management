# routes/chat.py - MCP Chat Router with Ollama Integration
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from services.mcp_service import MCPService, ChatResponse
from datetime import datetime
import uuid

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"]
)

# Initialize MCP service
mcp_service = MCPService()

# In-memory session storage (replace with Redis/DB in production)
sessions: Dict[str, Dict] = {}

# Request/Response Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    include_context: bool = Field(True, description="Include conversation history")

class ChatMessageHistory(BaseModel):
    user: str
    assistant: str
    timestamp: datetime

class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    last_activity: datetime
    message_count: int

# Endpoints
@router.post("/message", response_model=ChatResponse)
async def process_message(request: ChatRequest):
    """
    Process a chat message through MCP with Ollama integration
    
    Example:
    ```json
    {
        "message": "Calculate payment for $50,000 at 8.5% for 5 years",
        "session_id": "optional-session-id",
        "include_context": true
    }
    ```
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            sessions[session_id] = {
                "created_at": datetime.now(),
                "history": [],
                "context": {}
            }
        
        session = sessions[session_id]
        session["last_activity"] = datetime.now()
        
        context = None
        if request.include_context:
            context = {
                "history": session["history"],
                "session_data": session.get("context", {})
            }
        
        response = await mcp_service.process_query(
            message=request.message,
            session_id=session_id,
            context=context
        )
        
        session["history"].append({
            "user": request.message,
            "assistant": response.response,
            "timestamp": response.timestamp.isoformat()
        })
        
        if len(session["history"]) > 10:
            session["history"] = session["history"][-10:]
        
        response_dict = response.dict()
        response_dict["session_id"] = session_id
        
        return response_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """
    Get information about a chat session
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    return SessionInfo(
        session_id=session_id,
        created_at=session["created_at"],
        last_activity=session.get("last_activity", session["created_at"]),
        message_count=len(session["history"])
    )

@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 10):
    """
    Get chat history for a session
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = sessions[session_id]["history"]
    
    # Return last N messages
    return {
        "session_id": session_id,
        "history": history[-limit:] if limit > 0 else history,
        "total_messages": len(history)
    }

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a chat session
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    
    return {"message": "Session deleted successfully", "session_id": session_id}

@router.post("/session/{session_id}/clear")
async def clear_session_history(session_id: str):
    """
    Clear chat history for a session but keep the session
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[session_id]["history"] = []
    sessions[session_id]["last_activity"] = datetime.now()
    
    return {"message": "Session history cleared", "session_id": session_id}

@router.get("/health")
async def health_check():
    """
    Check health of chat service and Ollama connection
    """
    import httpx
    from services.mcp_service import OLLAMA_BASE_URL, ENABLE_OLLAMA
    
    ollama_status = "disabled"
    
    if ENABLE_OLLAMA:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                if response.status_code == 200:
                    ollama_status = "connected"
                else:
                    ollama_status = "error"
        except Exception:
            ollama_status = "unreachable"
    
    return {
        "status": "healthy",
        "service": "mcp_chat",
        "ollama_status": ollama_status,
        "active_sessions": len(sessions),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/stats")
async def get_stats():
    """
    Get service statistics
    """
    total_messages = sum(len(session["history"]) for session in sessions.values())
    
    return {
        "active_sessions": len(sessions),
        "total_messages": total_messages,
        "timestamp": datetime.now().isoformat()
    }