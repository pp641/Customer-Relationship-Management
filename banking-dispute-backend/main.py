import logging
import os
from fastapi import FastAPI, Depends
import redis
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import (
    ServerSelectionTimeoutError,
    ConfigurationError,
    OperationFailure
)
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
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
            'ses_smtp_region': os.getenv("AWS_REGION"),
            'ses_smtp_port': int(os.getenv("SES_SMTP_PORT", "587")),
            'ses_smtp_user': os.getenv("SES_SMTP_USER"),
            'ses_smtp_pass': os.getenv("SES_SMTP_PASS"),
            'redis_url': os.getenv("REDIS_URL", "redis://localhost:6379/0")
        }

# Global app state instance
app_state = AppState()

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
        
        # Determine if using local or Atlas MongoDB
        use_local = app_state.config.get('use_local_mongo', False)
        
        # Configure connection options
        connection_options = {
            'serverSelectionTimeoutMS': 5000,
            'connectTimeoutMS': 20000,
            'socketTimeoutMS': 20000,
        }
        
        # Add SSL/TLS options for Atlas
        if not use_local and 'mongodb+srv' in app_state.config['mongo_uri']:
            connection_options.update({
                'tls': True,
                'tlsAllowInvalidCertificates': False,  # Set to True only for testing
            })
            app_state.logger.info("Using MongoDB Atlas with SSL/TLS")
        else:
            app_state.logger.info("Using local MongoDB")
        
        # Create MongoDB client
        app_state.mongodb_client = MongoClient(
            app_state.config['mongo_uri'],
            **connection_options
        )
        
        # Test the connection
        app_state.mongodb_client.admin.command('ping')
        
        # Get database
        db = app_state.mongodb_client[app_state.config['mongo_db']]
        app_state.database = Database(db)
        
        # Set the database in dependencies module
        dependencies.set_database(app_state.database)
        
        app_state.logger.info("✅ MongoDB connection successful")
        app_state.logger.info(f"📊 Connected to database: {app_state.config['mongo_db']}")
        return True
        
    except ServerSelectionTimeoutError as e:
        app_state.logger.error(f"❌ MongoDB connection timeout: {e}")
        app_state.logger.error("Check if MongoDB server is accessible and credentials are correct")
        app_state.logger.error(f"Connection string: {app_state.config['mongo_uri'][:50]}...")
        return False
        
    except ConfigurationError as e:
        app_state.logger.error(f"❌ MongoDB configuration error: {e}")
        app_state.logger.error("Check your MongoDB URI format and SSL settings")
        return False
        
    except OperationFailure as e:
        app_state.logger.error(f"❌ MongoDB authentication failed: {e}")
        app_state.logger.error("Check your MongoDB username and password")
        return False
        
    except Exception as e:
        app_state.logger.error(f"❌ MongoDB connection failed: {e}")
        app_state.logger.error(f"Error type: {type(e).__name__}")
        
        # Check for SSL-specific errors
        if "SSL" in str(e) or "TLS" in str(e):
            app_state.logger.error("SSL/TLS Error detected. Try one of these solutions:")
            app_state.logger.error("1. Set USE_LOCAL_MONGO=true to use local MongoDB")
            app_state.logger.error("2. Update Dockerfile to install SSL certificates")
            app_state.logger.error("3. Set tlsAllowInvalidCertificates=true (not recommended for production)")
        
        app_state.logger.error(f"Connection string: {app_state.config['mongo_uri'][:50]}...")
        return False



def setup_smtp():
    try:
        # Load credentials from environment variables (NEVER hardcode)
        load_dotenv()
        
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_REGION')

        
        
        if not access_key or not secret_key:
            raise ValueError("AWS credentials not found in environment variables")
        
        # Create SES client
        ses_client = boto3.client(
            'ses',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Test the connection by calling a simple API
        app_state.logger.info("Testing SES connection...")
        
        # Test 1: Check if SES is enabled
        response = ses_client.get_account_sending_enabled()
        app_state.logger.info(f"SES sending enabled: {response.get('Enabled', False)}")
        
        # Test 2: Get sending quota
        quota_response = ses_client.get_send_quota()
        app_state.logger.info(f"Daily send quota: {quota_response.get('Max24HourSend', 0)}")
        app_state.logger.info(f"Current sent count: {quota_response.get('SentLast24Hours', 0)}")
        
        # Test 3: List verified email addresses
        identities = ses_client.list_verified_email_addresses()
        verified_emails = identities.get('VerifiedEmailAddresses', [])
        app_state.logger.info(f"Verified email addresses: {verified_emails}")
        
        # Store the client
        app_state.smtp_server = ses_client  # Use ses_client, not smtp_server
        
        # Set in dependencies
        dependencies.set_smtp_server(app_state.smtp_server)
        
        app_state.logger.info("✅ AWS SES client connected and tested successfully")
        return True
        
    except ValueError as e:
        app_state.logger.error(f"❌ Configuration error: {e}")
        return False
    except NoCredentialsError:
        app_state.logger.error("❌ AWS credentials not found")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        app_state.logger.error(f"❌ AWS SES ClientError [{error_code}]: {error_message}")
        return False
    except Exception as e:
        app_state.logger.error(f"❌ SES setup failed: {e}")
        return False





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
    from routers.banks import router as bank_router
    
    app.include_router(auth_router)
    app.include_router(bank_router)
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
