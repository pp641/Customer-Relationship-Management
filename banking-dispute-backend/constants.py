
from enum import Enum
from typing import Dict
import os

# Ollama configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Banking information
BANKS = [
    "State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank",
    "Punjab National Bank", "Bank of Baroda", "Canara Bank", "Other"
]

BANK_HELPLINES = {
    "State Bank of India": "1800 1111 109",
    "HDFC Bank": "1800 2611 232",
    "ICICI Bank": "1800 2000 888",
    "Axis Bank": "1800 4196 4444",
    "Punjab National Bank": "1800 2222 244",
    "Bank of Baroda": "1800 2580 244",
    "Canara Bank": "1800 4250 0018"
}

# Enums
class DisputeType(str, Enum):
    DOUBLE_DEBIT = "Double Debit / Duplicate Charge"
    UNAUTHORIZED = "Unauthorized Transaction"
    MISSING_REFUND = "Missing Refund"
    WRONG_AMOUNT = "Wrong Balance/Amount"
    FAILED_TRANSACTION = "Failed Transaction"
    ATM_DISPUTE = "ATM Dispute"
    MERCHANT_FRAUD = "Merchant Fraud"
    CARD_SKIMMING = "Card Skimming"
    OTHER = "Other"

class DisputeStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# App configuration
APP_CONFIG = {
    "title": "Banking Dispute Resolution API",
    "description": "AI-powered chatbot for banking dispute resolution using Ollama",
    "version": "1.0.0"
}

# CORS settings
CORS_SETTINGS = {
    "allow_origins": ["http://localhost:5173" , "http://127.0.0.1:5173"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

# Ollama settings
OLLAMA_OPTIONS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 200
}

# Chat flow constants
MAIN_MENU_OPTIONS = [
    "Report a Dispute",
    "Track Existing Dispute", 
    "Get Guidance",
    "Emergency Help"
]

GUIDANCE_TOPICS = [
    "Unauthorized Transaction",
    "Duplicate Charge", 
    "ATM Dispute",
    "Merchant Issues"
]