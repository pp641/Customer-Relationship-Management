import logging
from database import Database
import redis
import boto3




_database_instance: Database | None = None
_logger_instance: logging.Logger | None = None
_smtp_server = None
_config: dict | None = None
_redis: redis.Redis | None = None


def set_database(db: Database):
    global _database_instance
    _database_instance = db

def set_redis_client(redis: dict):
    global _redis
    _redis = redis


def set_logger(logger: logging.Logger):
    global _logger_instance
    _logger_instance = logger


def set_smtp_server(smtp):
    global _smtp_server
    _smtp_server = smtp


def set_config(config: dict):
    global _config
    _config = config


# Dependency functions for FastAPI
def get_database() -> Database:
    if _database_instance is None:
        raise RuntimeError(
            "Database not initialized. Please check your MongoDB credentials and connection string."
        )
    return _database_instance


def get_logger() -> logging.Logger:
    if _logger_instance is None:
        raise RuntimeError("Logger not initialized")
    return _logger_instance


def get_smtp_server():
    if _smtp_server is None:
        raise RuntimeError("SMTP client not initialized")
    return _smtp_server


def get_config() -> dict:
    if _config is None:
        raise RuntimeError("Config not initialized")
    return _config



def get_redis_client() -> redis.Redis:
    if _redis is None:
        raise RuntimeError("Redis client not initialized")
    return _redis
