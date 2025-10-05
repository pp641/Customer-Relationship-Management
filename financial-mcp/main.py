from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat, financial
import uvicorn

app = FastAPI(
    title="Financial Services MCP with Ollama",
    description="Intelligent loan servicing chatbot with Ollama integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(financial.router)

@app.get("/")
async def root():
    return {
        "message": "Financial Services MCP with Ollama",
        "docs": "/docs",
        "health": "/api/chat/health"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)