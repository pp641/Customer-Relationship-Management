import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
import httpx
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from auth import router as auth_router
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Banking Dispute Resolution API",
    description="AI-powered chatbot for banking dispute resolution using Ollama",
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

# Ollama configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")  # Default to llama2, can use llama3, mistral, etc.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

app.include_router(auth_router)


# Test Ollama connection on startup
async def test_ollama_connection():
    """Test if Ollama is running and model is available"""
    try:
        # Check if Ollama is running
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]
                logger.info(f"Available Ollama models: {available_models}")

                if OLLAMA_MODEL not in available_models:
                    logger.warning(f"Model {OLLAMA_MODEL} not found. Available models: {available_models}")
                    # Try to pull the model
                    logger.info(f"Attempting to pull model {OLLAMA_MODEL}...")
                    pull_response = await client.post(f"{OLLAMA_HOST}/api/pull",
                                                      json={"name": OLLAMA_MODEL})
                    if pull_response.status_code == 200:
                        logger.info(f"Successfully pulled {OLLAMA_MODEL}")
                    else:
                        logger.error(f"Failed to pull {OLLAMA_MODEL}")

                return True
            else:
                logger.error(f"Ollama not responding: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {str(e)}")
        logger.info("Make sure Ollama is running: ollama serve")
        return False


# Pydantic models
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


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}


class DisputeForm(BaseModel):
    type: Optional[DisputeType] = None
    bank: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    description: Optional[str] = None
    cardlastfour: Optional[str] = None
    priority: Optional[Priority] = None


class DisputeData(BaseModel):
    id: str = Field(default_factory=lambda: f"DSP{uuid.uuid4().hex[:8].upper()}")
    type: DisputeType
    amount: float
    date: str
    description: str
    status: DisputeStatus = DisputeStatus.SUBMITTED
    priority: Priority
    bank: str
    cardlastfour: str
    createdAt: str = Field(default_factory=lambda: datetime.now().isoformat())


class ChatResponse(BaseModel):
    response: str
    options: Optional[List[str]] = None
    action: Optional[str] = None
    dispute_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}


# In-memory storage (replace with database in production)
disputes_db: Dict[str, DisputeData] = {}
chat_sessions: Dict[str, Dict] = {}

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


# MCP Server Integration (Mock implementation)
class MCPServer:
    @staticmethod
    async def get_dispute_templates(dispute_type: str) -> str:
        """Get dispute resolution templates from MCP server"""
        templates = {
            "Double Debit / Duplicate Charge": """
Subject: Dispute for Duplicate Transaction

Dear Sir/Madam,
I am writing to dispute a duplicate transaction on my account.

Transaction Details:
- Date: {date}
- Amount: ₹{amount}
- Card ending: {card_last4}

I request immediate investigation and reversal of the duplicate charge.

Regards,
{customer_name}
            """,
            "Unauthorized Transaction": """
Subject: Unauthorized Transaction Dispute

Dear Bank Manager,
I wish to report an unauthorized transaction on my account.

Transaction Details:
- Date: {date}
- Amount: ₹{amount}
- Description: {description}

I did not authorize this transaction and request immediate blocking of my card.

Sincerely,
{customer_name}
            """
        }
        return templates.get(dispute_type, templates["Unauthorized Transaction"])

    @staticmethod
    async def get_guidance_steps(dispute_type: str) -> List[Dict[str, str]]:
        """Get step-by-step guidance from MCP server"""
        guidance_map = {
            "Unauthorized Transaction": [
                {"step": "1", "action": "Block your card immediately", "urgency": "critical"},
                {"step": "2", "action": "File police complaint", "urgency": "high"},
                {"step": "3", "action": "Contact bank within 24 hours", "urgency": "critical"},
                {"step": "4", "action": "Submit written dispute", "urgency": "medium"}
            ],
            "Double Debit / Duplicate Charge": [
                {"step": "1", "action": "Contact merchant first", "urgency": "medium"},
                {"step": "2", "action": "Gather transaction proofs", "urgency": "high"},
                {"step": "3", "action": "File bank dispute if merchant unresponsive", "urgency": "medium"}
            ]
        }
        return guidance_map.get(dispute_type, guidance_map["Unauthorized Transaction"])


# Ollama integration
async def get_ai_response(message: str, context: Dict[str, Any] = {}) -> str:
    """Get response from Ollama model"""
    try:
        system_prompt = f"""You are a helpful banking dispute resolution assistant for Indian banks. Your role is to:
1. Help users report banking disputes
2. Provide guidance on dispute resolution according to RBI guidelines
3. Collect necessary information for dispute filing
4. Offer empathetic and professional support

Current context: {json.dumps(context)}

Guidelines:
- Respond professionally and empathetically
- Keep responses concise but helpful (max 2-3 sentences)
- Provide accurate information based on Indian banking regulations
- Be supportive and understanding of customer frustrations
- Guide users through the dispute process step by step

User message: {message}

Response:"""

        # Use Ollama client
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 200
                    }
                }
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return get_fallback_response(message)

    except Exception as e:
        logger.error(f"Ollama API error: {str(e)}")
        return get_fallback_response(message)


def get_fallback_response(message: str) -> str:
    """Fallback response when AI is unavailable"""
    message_lower = message.lower()

    if any(word in message_lower for word in ["unauthorized", "fraud", "stolen"]):
        return "This seems like an urgent unauthorized transaction. Please block your card immediately by calling your bank's helpline and report this fraud within 24 hours for best protection."

    elif any(word in message_lower for word in ["duplicate", "double", "charged twice"]):
        return "For duplicate charges, first contact the merchant to request a refund. If they don't respond within 7 days, file a dispute with your bank along with transaction proof."

    elif any(word in message_lower for word in ["atm", "cash", "withdrawal"]):
        return "For ATM disputes, immediately contact your bank with the transaction receipt and ATM location details. Most ATM issues are resolved within 2-3 business days."

    else:
        return "I understand you're facing a banking issue. Please contact your bank's helpline immediately, or let me help you file a dispute by selecting 'Report a Dispute'."


# API Routes
@app.on_event("startup")
async def startup_event():
    """Test Ollama connection on startup"""
    logger.info("Testing Ollama connection...")
    is_connected = await test_ollama_connection()
    if not is_connected:
        logger.warning("Ollama not available - using fallback responses")


@app.get("/")
async def root():
    return {"message": "Banking Dispute Resolution API with Ollama", "status": "active"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatMessage):
    """Main chat endpoint"""
    try:
        session_id = chat_request.session_id or str(uuid.uuid4())
        message = chat_request.message.lower().strip()

        # Initialize session if not exists
        if session_id not in chat_sessions:
            chat_sessions[session_id] = {
                "step": "greeting",
                "dispute_form": {},
                "context": {}
            }

        session = chat_sessions[session_id]
        context = {**session["context"], **chat_request.context}

        # Process message based on current step
        if session["step"] == "greeting":
            if any(word in message for word in ["hello", "hi", "help", "start"]):
                return ChatResponse(
                    response="Hello! I'm your Banking Dispute Assistant. I can help you resolve banking disputes quickly and effectively. How can I assist you today?",
                    options=[
                        "Report a Dispute",
                        "Track Existing Dispute",
                        "Get Guidance",
                        "Emergency Help"
                    ],
                    context={"session_id": session_id, "step": "main_menu"}
                )
            else:
                ai_response = await get_ai_response(message, context)
                return ChatResponse(
                    response=ai_response,
                    options=[
                        "Report a Dispute",
                        "Track Existing Dispute",
                        "Get Guidance",
                        "Emergency Help"
                    ],
                    context={"session_id": session_id}
                )

        # Handle main menu selections
        elif "report a dispute" in message or session["step"] == "main_menu":
            if "report a dispute" in message:
                session["step"] = "dispute_type"
                chat_sessions[session_id] = session
                return ChatResponse(
                    response="I'll help you report a dispute. What type of issue are you experiencing?",
                    options=[dt.value for dt in DisputeType],
                    context={"session_id": session_id}
                )

        elif "track existing dispute" in message:
            session["step"] = "track_dispute"
            chat_sessions[session_id] = session
            return ChatResponse(
                response="Please provide your dispute ID (starts with DSP) or reference number:",
                context={"session_id": session_id}
            )

        elif "get guidance" in message:
            return ChatResponse(
                response="""Here are some helpful resources for banking disputes:

• **Time is critical**: Contact your bank within 24 hours for unauthorized transactions
• **Gather evidence**: Save SMS alerts, receipts, and screenshots
• **File written complaint**: Submit formal dispute letter to your bank
• **Keep records**: Document all communications and reference numbers
• **Follow up**: Check status regularly and escalate if needed

Would you like detailed guidance for a specific type of dispute?""",
                options=["Unauthorized Transaction", "Duplicate Charge", "ATM Dispute", "Merchant Issues"],
                context={"session_id": session_id}
            )

        elif "emergency help" in message:
            helplines = "\n".join([f"**{bank}**: {number}" for bank, number in BANK_HELPLINES.items()])
            return ChatResponse(
                response=f"""🚨 **Emergency Actions for Banking Fraud:**

**Immediate Steps:**
• Block your card/account immediately
• Report fraud to bank within 2 hours for zero liability
• File police complaint for criminal activities
• Change all online banking passwords

**24/7 Bank Helplines:**
{helplines}

**RBI Banking Ombudsman**: 14448 (Toll-free)

Which bank do you need help with?""",
                options=BANKS,
                context={"session_id": session_id}
            )

        # Handle dispute form collection
        elif session["step"] == "dispute_type":
            # Check if message matches any dispute type
            selected_type = None
            for dt in DisputeType:
                if dt.value.lower() in message or message in dt.value.lower():
                    selected_type = dt
                    break

            if selected_type:
                session["dispute_form"]["type"] = selected_type.value
                session["step"] = "bank_selection"
                chat_sessions[session_id] = session

                return ChatResponse(
                    response=f"You've selected: **{selected_type.value}**\n\nWhich bank is involved in this dispute?",
                    options=BANKS,
                    context={"session_id": session_id}
                )
            else:
                return ChatResponse(
                    response="Please select one of the dispute types from the options below:",
                    options=[dt.value for dt in DisputeType],
                    context={"session_id": session_id}
                )

        elif session["step"] == "bank_selection":
            if any(bank.lower() in message for bank in BANKS):
                selected_bank = next(bank for bank in BANKS if bank.lower() in message)
                session["dispute_form"]["bank"] = selected_bank
                session["step"] = "amount_input"
                chat_sessions[session_id] = session

                helpline = BANK_HELPLINES.get(selected_bank, "Contact bank directly")
                return ChatResponse(
                    response=f"Bank: **{selected_bank}**\nHelpline: {helpline}\n\nWhat is the disputed amount? Please enter the amount in ₹ (e.g., 5000)",
                    context={"session_id": session_id}
                )

        elif session["step"] == "amount_input":
            # Extract amount from message
            import re
            amount_match = re.search(r'[\d,]+\.?\d*', message.replace(',', ''))
            if amount_match:
                amount = float(amount_match.group())
                session["dispute_form"]["amount"] = amount
                session["step"] = "date_input"
                chat_sessions[session_id] = session

                return ChatResponse(
                    response=f"Amount: ₹{amount:,.2f}\n\nWhen did this transaction occur? Please provide the date (e.g., 2024-01-15 or 15 Jan 2024)",
                    context={"session_id": session_id}
                )
            else:
                return ChatResponse(
                    response="Please enter a valid amount in numbers (e.g., 5000 or 1500.50)",
                    context={"session_id": session_id}
                )

        elif session["step"] == "date_input":
            # Simple date validation - in production, use proper date parsing
            if any(char.isdigit() for char in message) and len(message) >= 8:
                session["dispute_form"]["date"] = message
                session["step"] = "description_input"
                chat_sessions[session_id] = session

                return ChatResponse(
                    response=f"Date: {message}\n\nPlease provide a brief description of the dispute and what happened:",
                    context={"session_id": session_id}
                )
            else:
                return ChatResponse(
                    response="Please provide a valid date (e.g., 2024-01-15, 15/01/2024, or 15 Jan 2024)",
                    context={"session_id": session_id}
                )

        elif session["step"] == "description_input":
            session["dispute_form"]["description"] = message
            session["step"] = "card_info"
            chat_sessions[session_id] = session

            return ChatResponse(
                response="Please provide the last 4 digits of the card involved (e.g., 1234). If not card-related, type 'N/A':",
                context={"session_id": session_id}
            )

        elif session["step"] == "card_info":
            session["dispute_form"]["cardlastfour"] = message if message.upper() != "N/A" else "N/A"

            # Create dispute automatically
            try:
                dispute_form = DisputeForm(**session["dispute_form"])
                dispute_result = await create_dispute(dispute_form)

                # Clear session
                del chat_sessions[session_id]

                return ChatResponse(
                    response=f"""✅ **Dispute Created Successfully!**

**Dispute ID**: {dispute_result['dispute_id']}
**Priority**: {dispute_result['priority'].title()}
**Estimated Resolution**: {dispute_result['estimated_resolution']}

**Next Steps:**
1. Block your card immediately if fraud-related
2. File police complaint for unauthorized transactions
3. Contact your bank: {dispute_result['bank_contact']}
4. Keep this dispute ID for tracking

You can track your dispute anytime by providing the Dispute ID.""",
                    action="dispute_created",
                    dispute_id=dispute_result['dispute_id']
                )
            except Exception as e:
                logger.error(f"Error creating dispute: {str(e)}")
                return ChatResponse(
                    response="I encountered an error creating your dispute. Please try again or contact your bank directly.",
                    options=["Try Again", "Emergency Help"]
                )

        elif session["step"] == "track_dispute":
            # Handle dispute tracking
            dispute_id = message.upper().strip()
            if dispute_id.startswith("DSP") and len(dispute_id) == 11:
                if dispute_id in disputes_db:
                    dispute = disputes_db[dispute_id]
                    return ChatResponse(
                        response=f"""**Dispute Status**: {dispute.status.title().replace('_', ' ')}

**Details:**
• Type: {dispute.type}
• Amount: ₹{dispute.amount:,.2f}
• Bank: {dispute.bank}
• Created: {dispute.createdAt.split('T')[0]}
• Priority: {dispute.priority.title()}

**Timeline:**
✅ Submitted - {dispute.createdAt.split('T')[0]}
🔄 Under Review - Expected in 1-2 days
⏳ Resolution - Expected in 5-7 business days

Your dispute is being processed. You'll receive updates via SMS/email."""
                    )
                else:
                    return ChatResponse(
                        response="Dispute ID not found. Please check the ID and try again, or contact your bank directly."
                    )
            else:
                return ChatResponse(
                    response="Please provide a valid dispute ID (format: DSP12345678) or reference number."
                )

        # Use AI for complex interactions
        else:
            ai_response = await get_ai_response(chat_request.message, context)
            return ChatResponse(
                response=ai_response,
                context={"session_id": session_id}
            )

    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return ChatResponse(
            response="I apologize for the technical issue. Please try again or contact your bank directly for immediate assistance.",
            options=["Try Again", "Emergency Help"]
        )


@app.post("/dispute", response_model=Dict[str, Any])
async def create_dispute(dispute: DisputeForm):
    """Create a new dispute"""
    try:
        # Determine priority based on amount and type
        priority = Priority.LOW
        if dispute.amount and dispute.amount > 50000:
            priority = Priority.HIGH
        elif dispute.amount and dispute.amount > 10000:
            priority = Priority.MEDIUM

        # High priority for fraud-related disputes
        if dispute.type in [DisputeType.UNAUTHORIZED, DisputeType.MERCHANT_FRAUD, DisputeType.CARD_SKIMMING]:
            priority = Priority.HIGH

        dispute_data = DisputeData(
            type=dispute.type,
            amount=dispute.amount,
            date=dispute.date,
            description=dispute.description,
            bank=dispute.bank,
            cardlastfour=dispute.cardlastfour,
            priority=priority
        )

        # Store in database
        disputes_db[dispute_data.id] = dispute_data

        # Get guidance steps from MCP server
        guidance_steps = await MCPServer.get_guidance_steps(dispute.type.value)

        return {
            "dispute_id": dispute_data.id,
            "status": "created",
            "priority": priority.value,
            "next_steps": guidance_steps,
            "estimated_resolution": "5-7 business days" if priority != Priority.HIGH else "2-3 business days",
            "bank_contact": BANK_HELPLINES.get(dispute.bank, "Contact your bank"),
            "created_at": dispute_data.createdAt
        }

    except Exception as e:
        logger.error(f"Dispute creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create dispute")


@app.get("/dispute/{dispute_id}")
async def get_dispute(dispute_id: str):
    """Get dispute by ID"""
    if dispute_id not in disputes_db:
        raise HTTPException(status_code=404, detail="Dispute not found")

    dispute = disputes_db[dispute_id]
    return {
        "dispute": dispute,
        "timeline": [
            {"date": dispute.createdAt, "status": "Submitted", "description": "Dispute submitted successfully"},
            {"date": (datetime.fromisoformat(dispute.createdAt.replace('Z', '+00:00').split('+')[0]) + timedelta(
                hours=2)).isoformat(),
             "status": "Acknowledged", "description": "Bank acknowledged receipt"},
            {"date": (datetime.fromisoformat(dispute.createdAt.replace('Z', '+00:00').split('+')[0]) + timedelta(
                days=1)).isoformat(),
             "status": "Under Review", "description": "Investigation started"}
        ]
    }


@app.get("/disputes")
async def list_disputes(status: Optional[DisputeStatus] = None, bank: Optional[str] = None):
    """List all disputes with optional filtering"""
    filtered_disputes = list(disputes_db.values())

    if status:
        filtered_disputes = [d for d in filtered_disputes if d.status == status]
    if bank:
        filtered_disputes = [d for d in filtered_disputes if d.bank.lower() == bank.lower()]

    return {
        "disputes": filtered_disputes,
        "total": len(filtered_disputes),
        "summary": {
            "by_status": {status.value: len([d for d in disputes_db.values() if d.status == status])
                          for status in DisputeStatus},
            "by_priority": {priority.value: len([d for d in disputes_db.values() if d.priority == priority])
                            for priority in Priority}
        }
    }


@app.post("/guidance/{dispute_type}")
async def get_guidance(dispute_type: str):
    """Get guidance for specific dispute type"""
    try:
        # Get guidance from MCP server
        steps = await MCPServer.get_guidance_steps(dispute_type)
        template = await MCPServer.get_dispute_templates(dispute_type)

        return {
            "dispute_type": dispute_type,
            "guidance_steps": steps,
            "complaint_template": template,
            "important_documents": [
                "Bank statement showing the transaction",
                "SMS alerts from bank",
                "Transaction receipt/screenshot",
                "Card blocking confirmation (if applicable)",
                "Communication with merchant (if applicable)",
                "Police complaint (for fraud cases)"
            ],
            "time_limits": {
                "report_to_bank": "Within 3 days for best results",
                "written_complaint": "Within 30 days of statement",
                "rbi_ombudsman": "Within 30 days if bank doesn't respond"
            }
        }
    except Exception as e:
        logger.error(f"Guidance error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get guidance")


@app.get("/banks")
async def get_banks():
    """Get list of supported banks with contact information"""
    bank_info = []
    for bank in BANKS:
        info = {
            "name": bank,
            "helpline": BANK_HELPLINES.get(bank, "Contact bank directly"),
            "dispute_email": f"disputes@{bank.lower().replace(' ', '')}.com" if bank != "Other" else None,
            "online_portal": f"https://{bank.lower().replace(' ', '')}.com/disputes" if bank != "Other" else None
        }
        bank_info.append(info)

    return {"banks": bank_info}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Test Ollama connection
    ollama_status = "disconnected"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags")
            if response.status_code == 200:
                ollama_status = "connected"
    except:
        ollama_status = "disconnected"

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "ollama": ollama_status,
            "model": OLLAMA_MODEL,
            "mcp_server": "active",
            "database": "active"
        }
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Process message (similar to chat endpoint)
            chat_request = ChatMessage(**message_data)
            chat_request.session_id = session_id
            response = await chat_endpoint(chat_request)

            # Send response back
            await websocket.send_text(response.json())

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)