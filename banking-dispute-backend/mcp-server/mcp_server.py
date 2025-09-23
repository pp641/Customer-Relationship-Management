# MCP (Model Context Protocol) Server for Banking Dispute Resolution
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import httpx
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Banking Dispute MCP Server",
    description="Model Context Protocol server for banking dispute templates and guidance",
    version="1.0.0"
)

# Data models
class Template(BaseModel):
    id: str
    name: str
    category: str
    subject: str
    content: str
    variables: List[str]
    language: str = "en"
    created_at: str

class GuidanceStep(BaseModel):
    step_number: int
    title: str
    description: str
    urgency: str  # critical, high, medium, low
    estimated_time: str
    required_documents: List[str]
    tips: List[str]

class DisputeKnowledge(BaseModel):
    dispute_type: str
    description: str
    common_causes: List[str]
    resolution_time: str
    success_rate: float
    legal_references: List[str]

# Knowledge base storage
TEMPLATES_DIR = Path("templates")
KNOWLEDGE_DIR = Path("knowledge")

# Create directories if they don't exist
TEMPLATES_DIR.mkdir(exist_ok=True)
KNOWLEDGE_DIR.mkdir(exist_ok=True)

# In-memory storage (replace with database in production)
templates_db: Dict[str, Template] = {}
guidance_db: Dict[str, List[GuidanceStep]] = {}
knowledge_db: Dict[str, DisputeKnowledge] = {}

# Initialize default templates
DEFAULT_TEMPLATES = {
    "unauthorized_transaction": Template(
        id="unauth_001",
        name="Unauthorized Transaction Dispute",
        category="fraud",
        subject="Urgent: Unauthorized Transaction Dispute - Account {account_number}",
        content="""Subject: Urgent: Unauthorized Transaction Dispute

Dear Bank Manager,

I am writing to formally report an unauthorized transaction on my account and request immediate investigation.

Account Details:
- Account Number: {account_number}
- Customer ID: {customer_id}
- Contact Number: {phone_number}

Transaction Details:
- Date: {transaction_date}
- Time: {transaction_time}
- Amount: ₹{amount}
- Transaction Reference: {reference_number}
- Card Last 4 Digits: {card_last4}
- Location/Merchant: {merchant_details}

Description of Issue:
{description}

I confirm that:
1. I did not authorize this transaction
2. I was not in possession of my card at the time if applicable
3. I have not shared my PIN/OTP with anyone
4. I noticed this transaction on {discovery_date}

Immediate Actions Taken:
- Card blocked on {block_date}
- Police complaint filed: {police_complaint_number}

I request:
1. Immediate reversal of the unauthorized amount
2. Detailed investigation of this transaction
3. Written confirmation of the dispute registration
4. Updates on the investigation progress

I am available at {phone_number} or {email} for any clarifications.

Thank you for your urgent attention to this matter.

Sincerely,
{customer_name}
{customer_address}
Date: {complaint_date}

Attachments:
- Copy of account statement
- Transaction screenshots
- Card blocking confirmation
- Police complaint copy
- ID proof copy""",
        variables=[
            "account_number", "customer_id", "phone_number", "transaction_date",
            "transaction_time", "amount", "reference_number", "card_last4",
            "merchant_details", "description", "discovery_date", "block_date",
            "police_complaint_number", "customer_name", "customer_address",
            "complaint_date", "email"
        ],
        created_at=datetime.now().isoformat()
    ),
    
    "duplicate_charge": Template(
        id="dup_001",
        name="Duplicate Charge Dispute",
        category="billing",
        subject="Dispute Resolution Request - Duplicate Transaction",
        content="""Subject: Dispute Resolution Request - Duplicate Transaction

Dear Customer Service Manager,

I am writing to dispute a duplicate charge on my account.

Account Information:
- Account Number: {account_number}
- Customer Name: {customer_name}
- Contact: {phone_number}

Transaction Details:
- Original Transaction Date: {original_date}
- Duplicate Transaction Date: {duplicate_date}
- Amount: ₹{amount}
- Merchant: {merchant_name}
- Reference Numbers: {original_ref}, {duplicate_ref}

Issue Description:
{description}

I have verified that:
1. Only one transaction was intended
2. I have receipts for the single purchase
3. The merchant has confirmed the duplicate charge
4. Both transactions appear on my statement dated {statement_date}

Supporting Evidence:
- Original purchase receipt attached
- Bank statement showing both transactions
- Merchant communication confirming error

Requested Action:
Please reverse the duplicate charge of ₹{amount} and provide written confirmation.

Contact Information:
- Phone: {phone_number}
- Email: {email}
- Best time to reach: {contact_time}

Thank you for your prompt attention.

Regards,
{customer_name}
Date: {complaint_date}""",
        variables=[
            "account_number", "customer_name", "phone_number", "original_date",
            "duplicate_date", "amount", "merchant_name", "original_ref",
            "duplicate_ref", "description", "statement_date", "email",
            "contact_time", "complaint_date"
        ],
        created_at=datetime.now().isoformat()
    ),
    
    "atm_dispute": Template(
        id="atm_001",
        name="ATM Dispute Template",
        category="atm",
        subject="ATM Transaction Dispute - {atm_location}",
        content="""Subject: ATM Transaction Dispute

Dear Branch Manager,

I want to report a disputed ATM transaction and request investigation.

Personal Details:
- Account Number: {account_number}
- Customer ID: {customer_id}
- Name: {customer_name}
- Phone: {phone_number}

ATM Transaction Details:
- Date: {transaction_date}
- Time: {transaction_time}
- ATM Location: {atm_location}
- ATM ID: {atm_id}
- Requested Amount: ₹{requested_amount}
- Transaction Type: {transaction_type}

Issue Description:
{issue_description}

Problem Details:
□ Amount debited but cash not dispensed
□ Partial cash dispensed
□ ATM card stuck/damaged
□ Wrong amount dispensed
□ Double debit
□ Other: {other_details}

Evidence Provided:
- ATM receipt attached
- Account statement showing debit
- Photos of ATM screen (if applicable)
- Video recording (if available)

Witness Information:
- Name: {witness_name}
- Contact: {witness_contact}

I request immediate investigation and reversal of the incorrect amount.

Available for contact:
- Phone: {phone_number}
- Email: {email}
- Preferred time: {contact_preference}

Sincerely,
{customer_name}
Date: {complaint_date}""",
        variables=[
            "account_number", "customer_id", "customer_name", "phone_number",
            "transaction_date", "transaction_time", "atm_location", "atm_id",
            "requested_amount", "transaction_type", "issue_description",
            "other_details", "witness_name", "witness_contact", "email",
            "contact_preference", "complaint_date"
        ],
        created_at=datetime.now().isoformat()
    )
}

# Initialize default guidance
DEFAULT_GUIDANCE = {
    "Unauthorized-Transaction": [
        GuidanceStep(
            step_number=1,
            title="Immediate Card Security",
            description="Block your debit/credit card immediately to prevent further unauthorized transactions",
            urgency="critical",
            estimated_time="2-5 minutes",
            required_documents=[],
            tips=[
                "Call the 24/7 helpline number on the back of your card",
                "Use mobile banking app to block card instantly",
                "Note down the card blocking reference number",
                "Block all cards if you're unsure which one was compromised"
            ]
        ),
        GuidanceStep(
            step_number=2,
            title="Contact Bank Immediately",
            description="Report the unauthorized transaction to your bank within 2-3 hours",
            urgency="critical",
            estimated_time="10-15 minutes",
            required_documents=["Account statement", "Transaction details"],
            tips=[
                "Call customer care immediately",
                "Email the dispute details to official email",
                "Request immediate investigation",
                "Get complaint reference number"
            ]
        ),
        GuidanceStep(
            step_number=3,
            title="File Police Complaint",
            description="For fraud transactions above ₹25,000, file a police complaint",
            urgency="high",
            estimated_time="30-60 minutes",
            required_documents=["ID proof", "Bank statement", "Transaction proof"],
            tips=[
                "Visit nearest police station",
                "File online FIR if available",
                "Get complaint number and copy",
                "Inform bank about police complaint"
            ]
        ),
        GuidanceStep(
            step_number=4,
            title="Gather Evidence",
            description="Collect all supporting documents for your dispute claim",
            urgency="high",
            estimated_time="20-30 minutes",
            required_documents=[
                "Bank statements", "SMS alerts", "Transaction receipts",
                "Card blocking confirmation", "Police complaint copy"
            ],
            tips=[
                "Screenshot all transaction alerts",
                "Print bank statements",
                "Save all SMS notifications",
                "Keep original receipts safe"
            ]
        ),
        GuidanceStep(
            step_number=5,
            title="Submit Written Complaint",
            description="Submit formal written complaint to bank with all evidence",
            urgency="medium",
            estimated_time="30-45 minutes",
            required_documents=[
                "Complaint letter", "Supporting documents", "ID proof copy"
            ],
            tips=[
                "Use official complaint template",
                "Submit in person if possible",
                "Keep acknowledgment receipt",
                "Follow up within 7 days"
            ]
        )
    ],
    
    "Duplicate-Charge": [
        GuidanceStep(
            step_number=1,
            title="Verify Transaction Details",
            description="Confirm the duplicate charge by checking your account statement carefully",
            urgency="medium",
            estimated_time="10-15 minutes",
            required_documents=["Bank statement", "Transaction receipts"],
            tips=[
                "Check transaction dates and amounts",
                "Verify merchant names match exactly",
                "Look for reference numbers",
                "Compare with your receipts"
            ]
        ),
        GuidanceStep(
            step_number=2,
            title="Contact Merchant First",
            description="Try to resolve with merchant before approaching bank",
            urgency="medium",
            estimated_time="15-30 minutes",
            required_documents=["Purchase receipt", "Bank statement"],
            tips=[
                "Call merchant customer service",
                "Email with transaction details",
                "Request refund for duplicate charge",
                "Get written confirmation if they agree"
            ]
        ),
        GuidanceStep(
            step_number=3,
            title="Bank Dispute Filing",
            description="If merchant doesn't respond in 3-5 days, file bank dispute",
            urgency="medium",
            estimated_time="20-30 minutes",
            required_documents=[
                "Bank statement", "Original receipt", "Merchant communication"
            ],
            tips=[
                "Use online banking dispute form",
                "Call customer care for assistance",
                "Provide all transaction details",
                "Keep dispute reference number"
            ]
        )
    ]
}

# Initialize default knowledge base
DEFAULT_KNOWLEDGE = {
    "Unauthorized-Transaction": DisputeKnowledge(
        dispute_type="Unauthorized Transaction",
        description="Transactions made without cardholder's knowledge or consent",
        common_causes=[
            "Card cloning/skimming",
            "Online fraud",
            "Lost or stolen card usage",
            "PIN compromise",
            "Phishing attacks"
        ],
        resolution_time="7-14 days",
        success_rate=0.89,
        legal_references=[
            "RBI Master Direction on Card Transactions",
            "Payment and Settlement Systems Act, 2007",
            "Information Technology Act, 2000"
        ]
    ),
    
    "Duplicate-Charge": DisputeKnowledge(
        dispute_type="Double Debit / Duplicate Charge",
        description="Same transaction charged multiple times due to system error",
        common_causes=[
            "Network timeouts",
            "System processing errors",
            "Merchant POS issues",
            "Double submission by customer",
            "Bank processing glitches"
        ],
        resolution_time="3-7 days",
        success_rate=0.95,
        legal_references=[
            "RBI Guidelines on Customer Protection",
            "Banking Ombudsman Scheme"
        ]
    )
}

# Initialize data
def init_data():
    templates_db.update(DEFAULT_TEMPLATES)
    guidance_db.update(DEFAULT_GUIDANCE)
    knowledge_db.update(DEFAULT_KNOWLEDGE)

init_data()

# API Routes
@app.get("/")
async def root():
    return {
        "service": "Banking Dispute MCP Server",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "templates": "/templates",
            "guidance": "/guidance",
            "knowledge": "/knowledge"
        }
    }

@app.get("/templates")
async def list_templates():
    """Get all available templates"""
    return {
        "templates": list(templates_db.values()),
        "count": len(templates_db)
    }

@app.get("/templates/{template_id}")
async def get_template(template_id: str):
    """Get specific template by ID"""
    if template_id not in templates_db:
        raise HTTPException(status_code=404, detail="Template not found")
    return templates_db[template_id]

@app.get("/templates/category/{category}")
async def get_templates_by_category(category: str):
    """Get templates by category"""
    filtered = [t for t in templates_db.values() if t.category == category]
    return {"templates": filtered, "count": len(filtered)}

@app.post("/templates/{template_id}/generate")
async def generate_template(template_id: str, variables: Dict[str, Any]):
    """Generate personalized template with provided variables"""
    if template_id not in templates_db:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = templates_db[template_id]
    
    try:
        # Replace variables in template content
        personalized_content = template.content
        personalized_subject = template.subject
        
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            personalized_content = personalized_content.replace(placeholder, str(var_value))
            personalized_subject = personalized_subject.replace(placeholder, str(var_value))
        
        return {
            "template_id": template_id,
            "subject": personalized_subject,
            "content": personalized_content,
            "generated_at": datetime.now().isoformat(),
            "variables_used": list(variables.keys()),
            "missing_variables": [var for var in template.variables if var not in variables]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Template generation failed: {str(e)}")

@app.get("/guidance")
async def list_guidance():
    """Get all guidance categories"""
    return {
        "categories": list(guidance_db.keys()),
        "total_steps": sum(len(steps) for steps in guidance_db.values())
    }

@app.get("/guidance/{dispute_type}")
async def get_guidance(dispute_type: str):
    """Get guidance steps for specific dispute type"""
    if dispute_type not in guidance_db:
        raise HTTPException(status_code=404, detail="Guidance not found for this dispute type")
    
    steps = guidance_db[dispute_type]
    return {
        "dispute_type": dispute_type,
        "steps": steps,
        "total_steps": len(steps),
        "critical_steps": len([s for s in steps if s.urgency == "critical"]),
        "estimated_total_time": _calculate_total_time(steps)
    }

@app.get("/knowledge")
async def list_knowledge():
    """Get all knowledge base entries"""
    return {
        "knowledge_base": list(knowledge_db.values()),
        "dispute_types": list(knowledge_db.keys())
    }

@app.get("/knowledge/{dispute_type}")
async def get_knowledge(dispute_type: str):
    """Get knowledge base entry for specific dispute type"""
    if dispute_type not in knowledge_db:
        raise HTTPException(status_code=404, detail="Knowledge not found for this dispute type")
    
    return knowledge_db[dispute_type]

@app.post("/analyze")
async def analyze_dispute_text(text: str, context: Optional[Dict[str, Any]] = None):
    """Analyze dispute description and suggest appropriate templates and guidance"""
    
    # Simple keyword-based analysis (can be enhanced with NLP models)
    keywords = {
        "unauthorized": ["unauthorized", "fraud", "stolen", "hacked", "without permission"],
        "duplicate": ["duplicate", "double", "charged twice", "same transaction"],
        "atm": ["atm", "cash machine", "withdrawal", "dispenser"],
        "missing_refund": ["refund", "return", "cancelled", "not received"],
        "wrong_amount": ["wrong amount", "incorrect", "different amount"]
    }
    
    text_lower = text.lower()
    detected_types = []
    
    for dispute_type, keywords_list in keywords.items():
        if any(keyword in text_lower for keyword in keywords_list):
            detected_types.append(dispute_type)
    
    # Get relevant templates and guidance
    suggestions = []
    for dtype in detected_types:
        if dtype == "unauthorized":
            suggestions.append({
                "dispute_type": "Unauthorized Transaction",
                "confidence": 0.85,
                "template_id": "unauth_001",
                "priority": "critical"
            })
        elif dtype == "duplicate":
            suggestions.append({
                "dispute_type": "Double Debit / Duplicate Charge", 
                "confidence": 0.90,
                "template_id": "dup_001",
                "priority": "medium"
            })
        elif dtype == "atm":
            suggestions.append({
                "dispute_type": "ATM Dispute",
                "confidence": 0.80,
                "template_id": "atm_001", 
                "priority": "high"
            })
    
    return {
        "analyzed_text": text,
        "detected_types": detected_types,
        "suggestions": suggestions,
        "confidence_threshold": 0.7,
        "analysis_timestamp": datetime.now().isoformat()
    }

@app.post("/guidance/personalized")
async def get_personalized_guidance(
    dispute_type: str,
    amount: Optional[float] = None,
    urgency: Optional[str] = None,
    customer_profile: Optional[Dict[str, Any]] = None
):
    """Get personalized guidance based on dispute details"""
    
    if dispute_type not in guidance_db:
        raise HTTPException(status_code=404, detail="Guidance not found")
    
    base_steps = guidance_db[dispute_type]
    personalized_steps = []
    
    for step in base_steps:
        # Modify steps based on amount
        modified_step = step.dict()
        
        if amount and amount > 50000:
            if "police" in step.description.lower():
                modified_step["urgency"] = "critical"
                modified_step["tips"].append(f"High amount (₹{amount}) - Police complaint mandatory")
        
        if amount and amount < 1000:
            if step.urgency == "high":
                modified_step["urgency"] = "medium"
                modified_step["tips"].append("Small amount - Bank resolution likely sufficient")
        
        personalized_steps.append(GuidanceStep(**modified_step))
    
    return {
        "dispute_type": dispute_type,
        "personalized_steps": personalized_steps,
        "customization_factors": {
            "amount": amount,
            "urgency_override": urgency,
            "customer_tier": customer_profile.get("tier") if customer_profile else None
        }
    }

@app.get("/compliance/rbi-guidelines")
async def get_rbi_guidelines():
    """Get RBI compliance guidelines for dispute resolution"""
    return {
        "guidelines": {
            "reporting_timeline": {
                "customer_to_bank": "Within 3 days of transaction",
                "bank_acknowledgment": "Within 24 hours",
                "provisional_credit": "Within 10 working days (if eligible)",
                "final_resolution": "Within 90 days"
            },
            "zero_liability_conditions": [
                "Contributory fraud/negligence not established",
                "Customer notified bank within 3 working days",
                "Loss reported before receiving monthly statement"
            ],
            "limited_liability": {
                "condition": "Customer delay in reporting 4-7 days",
                "limit": "₹10,000 or transaction amount (whichever is lower)"
            },
            "bank_responsibilities": [
                "Maintain transaction logs for 10 years",
                "Provide provisional credit for eligible cases",
                "Complete investigation within timeline",
                "Compensate for delays beyond 90 days"
            ]
        },
        "reference": "RBI/2017-18/15 - Master Direction on Card Transactions",
        "last_updated": "2023-03-15"
    }

@app.get("/stats/resolution")
async def get_resolution_statistics():
    """Get dispute resolution statistics"""
    return {
        "overall_stats": {
            "total_disputes_handled": 15420,
            "average_resolution_time": "6.2 days",
            "success_rate": "91.3%",
            "customer_satisfaction": "4.2/5"
        },
        "by_dispute_type": {
            "Unauthorized Transaction": {
                "volume": "45%",
                "avg_resolution": "8.5 days", 
                "success_rate": "89%"
            },
            "Double Debit": {
                "volume": "25%",
                "avg_resolution": "4.1 days",
                "success_rate": "96%"
            },
            "ATM Dispute": {
                "volume": "15%",
                "avg_resolution": "3.8 days", 
                "success_rate": "94%"
            },
            "Others": {
                "volume": "15%",
                "avg_resolution": "7.2 days",
                "success_rate": "87%"
            }
        },
        "monthly_trends": [
            {"month": "Oct 2023", "disputes": 1250, "resolved": 1145},
            {"month": "Nov 2023", "disputes": 1180, "resolved": 1089},
            {"month": "Dec 2023", "disputes": 1350, "resolved": 1242}
        ]
    }

@app.post("/validate/complaint")
async def validate_complaint(complaint_data: Dict[str, Any]):
    """Validate complaint data completeness"""
    
    required_fields = {
        "customer_name": "Customer name is required",
        "account_number": "Account number is required", 
        "transaction_date": "Transaction date is required",
        "amount": "Transaction amount is required",
        "description": "Issue description is required"
    }
    
    validation_errors = []
    missing_fields = []
    
    for field, error_msg in required_fields.items():
        if field not in complaint_data or not complaint_data[field]:
            missing_fields.append(field)
            validation_errors.append(error_msg)
    
    # Additional validations
    if "amount" in complaint_data:
        try:
            amount = float(complaint_data["amount"])
            if amount <= 0:
                validation_errors.append("Amount must be greater than 0")
        except (ValueError, TypeError):
            validation_errors.append("Amount must be a valid number")
    
    if "phone_number" in complaint_data:
        phone = str(complaint_data["phone_number"])
        if len(phone) != 10 or not phone.isdigit():
            validation_errors.append("Phone number must be 10 digits")
    
    completeness_score = ((len(required_fields) - len(missing_fields)) / len(required_fields)) * 100
    
    return {
        "is_valid": len(validation_errors) == 0,
        "validation_errors": validation_errors,
        "missing_fields": missing_fields,
        "completeness_score": completeness_score,
        "recommendations": _get_improvement_recommendations(missing_fields, complaint_data)
    }

def _calculate_total_time(steps: List[GuidanceStep]) -> str:
    """Calculate total estimated time for all steps"""
    total_minutes = 0
    for step in steps:
        # Parse time string (e.g., "10-15 minutes")
        time_str = step.estimated_time.lower()
        if "minute" in time_str:
            # Extract numbers and take average
            numbers = [int(x) for x in time_str.split() if x.isdigit()]
            if numbers:
                avg_time = sum(numbers) / len(numbers)
                total_minutes += avg_time
    
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes} minutes"

def _get_improvement_recommendations(missing_fields: List[str], data: Dict[str, Any]) -> List[str]:
    """Get recommendations to improve complaint"""
    recommendations = []
    
    if "description" in missing_fields:
        recommendations.append("Provide detailed description of the issue")
    
    if "transaction_date" in missing_fields:
        recommendations.append("Include exact transaction date and time")
    
    if "amount" in missing_fields:
        recommendations.append("Specify the disputed transaction amount")
    
    if data.get("amount", 0) > 25000 and "police_complaint" not in data:
        recommendations.append("Consider filing police complaint for high-value fraud")
    
    if "supporting_documents" not in data:
        recommendations.append("Attach supporting documents (statements, receipts)")
    
    return recommendations

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "templates": f"{len(templates_db)} templates loaded",
            "guidance": f"{len(guidance_db)} guidance categories",
            "knowledge": f"{len(knowledge_db)} knowledge entries"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)