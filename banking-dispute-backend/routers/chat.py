"""
Chat endpoints
"""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from models import ChatMessage, ChatResponse
from chat_handler import ChatHandler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    """Main chat endpoint"""
    return await ChatHandler.process_message(chat_request)


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            chat_request = ChatMessage(**message_data)
            chat_request.session_id = session_id
            response = await ChatHandler.process_message(chat_request)
            
            # Send response back
            await websocket.send_text(response.json())
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()
