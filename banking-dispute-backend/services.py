import json
import logging
from typing import List, Dict, Any
import httpx
from constants import OLLAMA_HOST, OLLAMA_MODEL, OLLAMA_OPTIONS

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for Ollama AI integration"""
    
    @staticmethod
    async def test_connection() -> bool:
        """Test if Ollama is running and model is available"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{OLLAMA_HOST}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    available_models = [model["name"] for model in models]
                    logger.info(f"Available Ollama models: {available_models}")

                    if OLLAMA_MODEL not in available_models:
                        logger.warning(f"Model {OLLAMA_MODEL} not found. Available models: {available_models}")
                        # Try to pull the model
                        logger.info(f"Attempting to pull model {OLLAMA_MODEL}...")
                        pull_response = await client.post(
                            f"{OLLAMA_HOST}/api/pull",
                            json={"name": OLLAMA_MODEL},
                            timeout=300.0  # 5 minutes for model pull
                        )
                        if pull_response.status_code == 200:
                            logger.info(f"Successfully pulled {OLLAMA_MODEL}")
                            return True
                        else:
                            logger.error(f"Failed to pull {OLLAMA_MODEL}")
                            return False

                    return True
                else:
                    logger.error(f"Ollama not responding: {response.status_code}")
                    return False
        except httpx.TimeoutException:
            logger.error("Ollama connection timeout")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {str(e)}")
            logger.info("Make sure Ollama is running: ollama serve")
            return False

    @staticmethod
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
- Always prioritize customer safety and fraud prevention

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
                        "options": OLLAMA_OPTIONS
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "").strip()
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return FallbackService.get_response(message)

        except httpx.TimeoutException:
            logger.error("Ollama API timeout")
            return FallbackService.get_response(message)
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            return FallbackService.get_response(message)


class FallbackService:
    """Fallback responses when AI is unavailable"""
    
    @staticmethod
    def get_response(message: str) -> str:
        """Fallback response when AI is unavailable"""
        message_lower = message.lower()

        # Urgent fraud-related responses
        if any(word in message_lower for word in ["unauthorized", "fraud", "stolen", "hacked"]):
            return ("🚨 This seems urgent! For unauthorized transactions: "
                   "1) Block your card IMMEDIATELY 2) Call your bank's helpline 3) Report within 24 hours for zero liability protection")

        # Duplicate charge responses
        elif any(word in message_lower for word in ["duplicate", "double", "charged twice", "same transaction"]):
            return ("For duplicate charges: 1) Contact the merchant first for a refund 2) If no response in 7 days, "
                   "file a dispute with your bank 3) Keep transaction receipts as proof")

        # ATM related issues
        elif any(word in message_lower for word in ["atm", "cash", "withdrawal", "dispense"]):
            return ("For ATM disputes: 1) Keep the transaction receipt 2) Note the ATM location and time "
                   "3) Contact your bank immediately with these details 4) Most ATM issues resolve in 2-3 business days")

        # Missing refund issues
        elif any(word in message_lower for word in ["refund", "return", "money back", "cancelled"]):
            return ("For missing refunds: 1) Check if the refund timeline has passed 2) Contact the merchant first "
                   "3) If merchant doesn't respond, file a dispute with your bank within 30 days")

        # General banking issues
        elif any(word in message_lower for word in ["wrong amount", "balance", "statement", "error"]):
            return ("For balance/amount disputes: 1) Check your bank statement carefully 2) Note the incorrect transaction details "
                   "3) Contact your bank within 3 days 4) File a written complaint for best results")

        # Greeting responses
        elif any(word in message_lower for word in ["hello", "hi", "help", "start", "support"]):
            return ("Hello! I'm here to help with banking disputes. I can assist you with: "
                   "• Reporting unauthorized transactions • Filing duplicate charge disputes • ATM issues • Tracking existing disputes")

        # Default helpful response
        else:
            return ("I understand you're facing a banking issue. For immediate help: "
                   "• Call your bank's helpline for urgent issues • Use 'Report a Dispute' to file a new complaint "
                   "• Select 'Emergency Help' for fraud situations • Choose 'Get Guidance' for general advice")


class MCPServer:
    """Mock MCP Server for dispute templates and guidance"""
    
    @staticmethod
    async def get_dispute_templates(dispute_type: str) -> str:
        """Get dispute resolution templates from MCP server"""
        templates = {
            "Double Debit / Duplicate Charge": """
Subject: Dispute for Duplicate Transaction - Account Number: [Your Account Number]

Dear Sir/Madam,

I am writing to dispute a duplicate/double charge on my account for the following transaction:

Transaction Details:
- Date: {date}
- Amount: ₹{amount}
- Merchant: {merchant_name}
- Card ending: {card_last4}
- Reference Number: {reference_number}

The same transaction has been charged twice to my account. I have only made one purchase/transaction but have been charged multiple times.

I request immediate investigation and reversal of the duplicate charge along with any applicable fees.

Attached documents:
- Bank statement showing duplicate charges
- Original transaction receipt
- SMS alerts from bank

I look forward to a prompt resolution within the RBI mandated timeline.

Regards,
[Your Name]
[Contact Details]
            """,
            
            "Unauthorized Transaction": """
Subject: Unauthorized Transaction Dispute - Immediate Action Required

Dear Bank Manager,

I wish to report an unauthorized transaction on my account and request immediate action:

Transaction Details:
- Date: {date}
- Time: {time}
- Amount: ₹{amount}
- Location: {location}
- Card ending: {card_last4}
- Reference: {reference_number}

IMPORTANT: I did not authorize this transaction. My card was in my possession at the time.

Immediate Actions Requested:
1. Block my card immediately
2. Investigate this fraudulent transaction
3. Reverse the unauthorized charge
4. Issue new card with different number

I am filing this complaint within 3 days as per RBI guidelines and expect zero liability protection.

Urgently,
[Your Name]
[Contact Details]
            """,
            
            "ATM Dispute": """
Subject: ATM Transaction Dispute - Cash Not Dispensed

Dear Sir/Madam,

I wish to report an ATM transaction where cash was not dispensed but my account was debited.

ATM Transaction Details:
- Date: {date}
- Time: {time}
- ATM Location: {atm_location}
- Amount Requested: ₹{amount}
- Transaction ID: {transaction_id}
- ATM ID: {atm_id}

Issue: The amount was debited from my account but cash was not dispensed from the ATM.

I have retained the transaction receipt and request immediate credit of the amount back to my account.

Attached: ATM receipt and bank statement

Please resolve this within 2-3 business days as per standard ATM dispute resolution timeline.

Regards,
[Your Name]
[Account Number]
            """,
            
            "Missing Refund": """
Subject: Missing Refund Claim - Transaction Cancelled

Dear Customer Service,

I am writing regarding a refund that has not been credited to my account for a cancelled transaction.

Original Transaction Details:
- Date: {transaction_date}
- Amount: ₹{amount}
- Merchant: {merchant_name}
- Cancellation Date: {cancellation_date}
- Refund Expected: {expected_refund_date}

The merchant has confirmed the cancellation and refund processing, but the amount has not been credited to my account within the expected timeline.

I request you to:
1. Track the refund status
2. Credit the amount if refund was processed by merchant
3. Provide timeline for resolution

Merchant refund confirmation and original transaction receipt are attached.

Thank you,
[Your Name]
[Contact Information]
            """
        }
        
        return templates.get(dispute_type, templates["Unauthorized Transaction"])

    @staticmethod
    async def get_guidance_steps(dispute_type: str) -> List[Dict[str, str]]:
        """Get step-by-step guidance from MCP server"""
        guidance_map = {
            "Unauthorized Transaction": [
                {"step": "1", "action": "Block your card immediately", "urgency": "critical", "timeline": "Immediately"},
                {"step": "2", "action": "Call bank helpline", "urgency": "critical", "timeline": "Within 2 hours"},
                {"step": "3", "action": "File police complaint", "urgency": "high", "timeline": "Within 24 hours"},
                {"step": "4", "action": "Submit written dispute to bank", "urgency": "high", "timeline": "Within 3 days"},
                {"step": "5", "action": "Follow up regularly", "urgency": "medium", "timeline": "Every 2-3 days"}
            ],
            "Double Debit / Duplicate Charge": [
                {"step": "1", "action": "Contact merchant first", "urgency": "medium", "timeline": "Within 2 days"},
                {"step": "2", "action": "Gather transaction proofs", "urgency": "high", "timeline": "Immediately"},
                {"step": "3", "action": "Wait for merchant response", "urgency": "low", "timeline": "7 days"},
                {"step": "4", "action": "File bank dispute if no merchant response", "urgency": "medium", "timeline": "After 7 days"},
                {"step": "5", "action": "Submit all documentation", "urgency": "high", "timeline": "With dispute filing"}
            ],
            "ATM Dispute": [
                {"step": "1", "action": "Keep ATM receipt", "urgency": "critical", "timeline": "Immediately"},
                {"step": "2", "action": "Note ATM location and time", "urgency": "high", "timeline": "Immediately"},
                {"step": "3", "action": "Contact bank immediately", "urgency": "critical", "timeline": "Within 2 hours"},
                {"step": "4", "action": "File written complaint", "urgency": "high", "timeline": "Within 24 hours"},
                {"step": "5", "action": "Follow up for resolution", "urgency": "medium", "timeline": "After 2-3 days"}
            ],
            "Missing Refund": [
                {"step": "1", "action": "Check refund timeline with merchant", "urgency": "medium", "timeline": "Immediately"},
                {"step": "2", "action": "Contact merchant for refund status", "urgency": "medium", "timeline": "After expected date"},
                {"step": "3", "action": "Get refund confirmation from merchant", "urgency": "high", "timeline": "Within 3 days"},
                {"step": "4", "action": "Contact bank if refund processed", "urgency": "high", "timeline": "After confirmation"},
                {"step": "5", "action": "File dispute with bank", "urgency": "medium", "timeline": "If no resolution in 15 days"}
            ]
        }
        return guidance_map.get(dispute_type, guidance_map["Unauthorized Transaction"])

    @staticmethod
    async def get_important_documents(dispute_type: str) -> List[str]:
        """Get list of important documents for dispute type"""
        document_map = {
            "Unauthorized Transaction": [
                "Bank statement showing unauthorized transaction",
                "SMS alerts from bank",
                "Card blocking confirmation",
                "Police complaint copy (if filed)",
                "ID proof copy",
                "Recent transaction history"
            ],
            "Double Debit / Duplicate Charge": [
                "Bank statement showing duplicate charges",
                "Original transaction receipt",
                "SMS alerts for both transactions",
                "Communication with merchant (emails/chat)",
                "Proof of single purchase/transaction"
            ],
            "ATM Dispute": [
                "ATM transaction receipt",
                "Bank statement showing debit",
                "Photo of ATM (if possible)",
                "SMS alert of transaction",
                "Written complaint copy"
            ],
            "Missing Refund": [
                "Original transaction receipt",
                "Cancellation/refund request proof",
                "Merchant refund confirmation",
                "Bank statement showing original debit",
                "Communication with merchant"
            ]
        }
        return document_map.get(dispute_type, document_map["Unauthorized Transaction"])
