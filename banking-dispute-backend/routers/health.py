"""
Health check and system status endpoints
"""
import httpx
from datetime import datetime
from fastapi import APIRouter
from models import HealthResponse
from constants import OLLAMA_HOST, OLLAMA_MODEL
from services import OllamaService

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Test Ollama connection
    ollama_status = "connected" if await OllamaService.test_connection() else "disconnected"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        services={
            "ollama": ollama_status,
            "model": OLLAMA_MODEL,
            "mcp_server": "active",
            "database": "active"
        }
    )


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Banking Dispute Resolution API with Ollama", 
        "status": "active",
        "version": "1.0.0"
    }
