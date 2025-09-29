import logging
import os
from fastapi import FastAPI, Depends
import redis
from fastapi.middleware.cors import CORSMiddleware
from constants import APP_CONFIG, CORS_SETTINGS
from dotenv import load_dotenv
from urllib.parse import quote_plus
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from services import OllamaService
from pymongo import MongoClient
import boto3
from database import Database
from typing import Optional
from contextlib import asynccontextmanager
import dependencies


# Load environment variables
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppState:
    """Container for global application state"""
    def __init__(self):
        self.mongodb_client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self.s3_client = None
        self.smtp_server = None
        self.redis_client: Optional[redis.Redis] = None
        self.logger = logger
        self.config = {
            'mongo_uri': f"mongodb+srv://{quote_plus(os.getenv('MONGO_USERNAME'))}:{quote_plus(os.getenv('MONGO_PASSWORD'))}@cluster0.vohszmp.mongodb.net/",
            'mongo_db': os.getenv("MONGO_DB"),
            'ses_smtp_host': os.getenv("SES_SMTP_HOST", "email-smtp.us-east-1.amazonaws.com"),
            'ses_smtp_port': int(os.getenv("SES_SMTP_PORT", "587")),
            'ses_smtp_user': os.getenv("SES_SMTP_USER"),
            'ses_smtp_pass': os.getenv("SES_SMTP_PASS"),
            'redis_url': os.getenv("REDIS_URL", "redis://localhost:6379/0")
        }

# Global app state instance
app_state = AppState()


# -----------------------------
# Setup Functions
# -----------------------------
async def setup_ollama():
    """Setup and test Ollama connection"""
    app_state.logger.info("Testing Ollama connection...")
    is_connected = await OllamaService.test_connection()
    if not is_connected:
        app_state.logger.warning("❌ Ollama not available - using fallback responses")
    else:
        app_state.logger.info("✅ Ollama connection successful")


def setup_mongodb():
    """Setup MongoDB connection using PyMongo"""
    try:
        app_state.logger.info("Connecting to MongoDB...")
        app_state.mongodb_client = MongoClient(
            app_state.config['mongo_uri'],
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        
        # Test the connection
        app_state.mongodb_client.admin.command('ping')
        
        # Get database
        db = app_state.mongodb_client[app_state.config['mongo_db']]
        app_state.database = Database(db)
        
        # Set the database in dependencies module
        dependencies.set_database(app_state.database)
        
        app_state.logger.info("✅ MongoDB connection successful")
        return True
    except Exception as e:
        app_state.logger.error(f"❌ MongoDB connection failed: {e}")
        app_state.logger.error(f"Connection string: {app_state.config['mongo_uri'][:50]}...")
        return False


def setup_smtp():
    """Setup SMTP connection for AWS SES"""
    try:
        server = smtplib.SMTP(
            app_state.config['ses_smtp_host'], 
            app_state.config['ses_smtp_port']
        )
        server.starttls()
        server.login(
            app_state.config['ses_smtp_user'], 
            app_state.config['ses_smtp_pass']
        )
        app_state.smtp_server = server
        
        # Set the SMTP server in dependencies module
        dependencies.set_smtp_server(app_state.smtp_server)
        
        app_state.logger.info("✅ SMTP server connected successfully")
    except Exception as e:
        app_state.logger.error(f"❌ SMTP setup failed: {e}")




def setup_redis():
    """Setup Redis connection"""
    try:
        app_state.redis_client = redis.Redis.from_url(
            app_state.config['redis_url'], decode_responses=True
        )
        # Test connection (synchronous)
        app_state.redis_client.ping()
        dependencies.set_redis_client(app_state.redis_client)
        app_state.logger.info("✅ Redis connection successful")
    except Exception as e:
        app_state.logger.error(f"❌ Redis connection failed: {e}")
        app_state.redis_client = None




# -----------------------------
# Lifespan Event Handler
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    app_state.logger.info("🚀 Starting Banking Dispute Resolution API...")
    
    # Set logger and config in dependencies module
    dependencies.set_logger(app_state.logger)
    dependencies.set_config(app_state.config)
    # Setup MongoDB first (most critical)
    mongo_success = setup_mongodb()
    if not mongo_success:
        app_state.logger.error("⚠️  MongoDB connection failed - API will not work properly!")
    
    # Setup other services
    await setup_ollama()
    setup_smtp()
    setup_redis()
    
    app_state.logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    app_state.logger.info("🛑 Shutting down application...")
    
    if app_state.mongodb_client:
        app_state.mongodb_client.close()
        app_state.logger.info("MongoDB connection closed")
    
    if app_state.smtp_server:
        try:
            app_state.smtp_server.quit()
            app_state.logger.info("SMTP connection closed")
        except:
            pass



def get_database() -> Database:
    """Dependency to get database instance"""
    return dependencies.get_database()


def get_logger() -> logging.Logger:
    """Dependency to get logger instance"""
    return dependencies.get_logger()


def get_smtp_server():
    """Dependency to get SMTP server instance"""
    return dependencies.get_smtp_server()


def get_config() -> dict:
    """Dependency to get configuration"""
    return dependencies.get_config()


def get_app_state() -> AppState:
    """Dependency to get entire app state (if needed)"""
    return app_state


def get_redis_client() -> redis.Redis:
    """Dependency to get Redis client instance"""
    return dependencies.get_redis_client()



# -----------------------------
# FastAPI App Creation
# -----------------------------
def create_app() -> FastAPI:
    """Factory function to create FastAPI app"""
    app = FastAPI(**APP_CONFIG, lifespan=lifespan)
    
    app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
    
    
    # Import routers here to avoid circular imports
    from routers.auth import router as auth_router
    
    app.include_router(auth_router)
    # app.include_router(chat.router)
    # app.include_router(disputes.router)
    # app.include_router(health.router)
    
    return app


# Initialize FastAPI app
app = create_app()


# Add a health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if app_state.database is not None else "disconnected",
        "smtp": "connected" if app_state.smtp_server is not None else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)