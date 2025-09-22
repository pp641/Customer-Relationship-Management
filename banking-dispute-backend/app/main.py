from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import openai
import asyncio
import json
import uuid
from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager
import httpx
import os
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Banking Dispute Resolution API",
    description="AI-powered chatbot for banking dispute resolution",
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

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")

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
    cardLast4: Optional[str] = None
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
    cardLast4: str
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
    async def get_dispute_templates(dispute_type: str) -> Dict[str, str]:
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

# OpenAI integration
async def get_ai_response(message: str, context: Dict[str, Any] = {}) -> str:
    """Get response from OpenAI GPT model"""
    try:
        system_prompt = f"""
        You are a helpful banking dispute resolution assistant. Your role is to:
        1. Help users report banking disputes
        2. Provide guidance on dispute resolution
        3. Collect necessary information for dispute filing
        4. Offer empathetic and professional support
        
        Current context: {json.dumps(context)}
        
        Respond professionally and empathetically. Keep responses concise but helpful.
        If asked about specific banking procedures, provide accurate information based on Indian banking regulations.
        """
        
        response = await asyncio.create_task(
            openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=300,
                temperature=0.7
            )
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again or contact your bank directly for immediate assistance."

# API Routes
@app.get("/")
async def root():
    return {"message": "Banking Dispute Resolution API", "status": "active"}

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
                    response="Hello! I'm your Banking Dispute Assistant. How can I help you today?",
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
                    ]
                )
        
        # Handle main menu selections
        elif "report a dispute" in message:
            session["step"] = "dispute_type"
            return ChatResponse(
                response="I'll help you report a dispute. What type of issue are you experiencing?",
                options=list(DisputeType.__members__.values())
            )
        
        elif "track existing dispute" in message:
            session["step"] = "track_dispute"
            return ChatResponse(
                response="Please provide your dispute ID or reference number:"
            )
        
        elif "get guidance" in message:
            return ChatResponse(
                response="""Here are some helpful resources:

• Always contact your bank within 24 hours
• Gather all transaction evidence (SMS, receipts, screenshots)  
• File a written complaint with your bank
• Keep records of all communications
• Follow up regularly on your case status

Would you like detailed guidance for a specific issue?""",
                options=["Unauthorized Transaction", "Duplicate Charge", "ATM Dispute", "General Tips"]
            )
        
        elif "emergency help" in message:
            helplines = "\n".join([f"**{bank}**: {number}" for bank, number in BANK_HELPLINES.items()])
            return ChatResponse(
                response=f"""🚨 **Emergency Actions:**

• Block your card immediately
• Report fraud to bank within 2 hours
• File police complaint for criminal activities

**24/7 Bank Helplines:**
{helplines}

Which bank do you need help with?""",
                options=BANKS
            )
        
        # Handle dispute form collection
        elif session["step"] == "dispute_type":
            if message in [dt.value.lower() for dt in DisputeType]:
                # Find matching dispute type
                dispute_type = next(dt for dt in DisputeType if dt.value.lower() == message)
                session["dispute_form"]["type"] = dispute_type.value
                session["step"] = "bank_selection"
                
                return ChatResponse(
                    response=f"You've selected: {dispute_type.value}\n\nWhich bank is involved?",
                    options=BANKS
                )
        
        elif session["step"] == "bank_selection":
            if message.title() in BANKS:
                session["dispute_form"]["bank"] = message.title()
                session["step"] = "amount_input"
                
                return ChatResponse(
                    response=f"Bank: {message.title()}\n\nWhat is the disputed amount? (Enter amount in ₹)"
                )
        
        # Use AI for complex interactions
        else:
            ai_response = await get_ai_response(message, context)
            return ChatResponse(response=ai_response)
            
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/dispute", response_model=Dict[str, Any])
async def create_dispute(dispute: DisputeForm):
    """Create a new dispute"""
    try:
        # Determine priority based on amount
        priority = Priority.LOW
        if dispute.amount and dispute.amount > 50000:
            priority = Priority.HIGH
        elif dispute.amount and dispute.amount > 10000:
            priority = Priority.MEDIUM
        
        dispute_data = DisputeData(
            type=dispute.type,
            amount=dispute.amount,
            date=dispute.date,
            description=dispute.description,
            bank=dispute.bank,
            cardLast4=dispute.cardLast4,
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
            "estimated_resolution": "5-7 business days",
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
            {"date": (datetime.fromisoformat(dispute.createdAt) + timedelta(hours=2)).isoformat(), 
             "status": "Acknowledged", "description": "Bank acknowledged receipt"},
            {"date": (datetime.fromisoformat(dispute.createdAt) + timedelta(days=1)).isoformat(), 
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

@app.post("/templates/{dispute_type}")
async def get_template(dispute_type: str, details: Dict[str, Any]):
    """Generate personalized complaint template"""
    try:
        base_template = await MCPServer.get_dispute_templates(dispute_type)
        
        # Personalize template
        personalized_template = base_template.format(
            date=details.get("date", "[Transaction Date]"),
            amount=details.get("amount", "[Amount]"),
            card_last4=details.get("cardLast4", "[Last 4 digits]"),
            description=details.get("description", "[Description]"),
            customer_name=details.get("customerName", "[Your Name]")
        )
        
        return {
            "template": personalized_template,
            "subject": f"Dispute Resolution Request - {dispute_type}",
            "attachments_needed": [
                "Copy of bank statement",
                "Transaction receipt",
                "ID proof copy",
                "Any supporting evidence"
            ]
        }
    except Exception as e:
        logger.error(f"Template generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate template")

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

@app.post("/notify")
async def send_notification(dispute_id: str, background_tasks: BackgroundTasks):
    """Send notification about dispute status"""
    if dispute_id not in disputes_db:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    # Add background task for notification
    background_tasks.add_task(send_sms_notification, dispute_id)
    
    return {"message": "Notification sent", "dispute_id": dispute_id}

async def send_sms_notification(dispute_id: str):
    """Background task to send SMS notification"""
    # Mock SMS sending - replace with actual SMS service
    dispute = disputes_db[dispute_id]
    logger.info(f"SMS sent for dispute {dispute_id}: Your dispute is being processed")

@app.get("/stats")
async def get_statistics():
    """Get dispute resolution statistics"""
    total_disputes = len(disputes_db)
    if total_disputes == 0:
        return {"message": "No disputes found"}
    
    stats = {
        "total_disputes": total_disputes,
        "resolution_rate": "87%",  # Mock data
        "average_resolution_time": "5.2 days",  # Mock data
        "by_status": {
            status.value: len([d for d in disputes_db.values() if d.status == status])
            for status in DisputeStatus
        },
        "by_type": {},
        "by_bank": {},
        "monthly_trend": [
            {"month": "Jan", "disputes": 45, "resolved": 39},
            {"month": "Feb", "disputes": 52, "resolved": 48},
            {"month": "Mar", "disputes": 38, "resolved": 35}
        ]
    }
    
    # Calculate type and bank distributions
    for dispute in disputes_db.values():
        stats["by_type"][dispute.type] = stats["by_type"].get(dispute.type, 0) + 1
        stats["by_bank"][dispute.bank] = stats["by_bank"].get(dispute.bank, 0) + 1
    
    return stats

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message (similar to chat endpoint)
            chat_request = ChatMessage(**message_data)
            response = await chat_endpoint(chat_request)
            
            # Send response back
            await websocket.send_text(response.json())
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "openai": "connected" if openai.api_key else "not configured",
            "mcp_server": "active",
            "database": "active"
        }
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)