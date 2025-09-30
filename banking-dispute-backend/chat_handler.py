"""
Chat conversation logic and flow management
"""
import re
import uuid
import logging
from typing import Dict, Any
from models import ChatMessage, ChatResponse, DisputeForm
from constants import DisputeType, BANKS, BANK_HELPLINES, MAIN_MENU_OPTIONS, GUIDANCE_TOPICS
from database import db
from services import OllamaService
from dispute_service import DisputeService

logger = logging.getLogger(__name__)


class ChatHandler:
    """Handles chat conversation flow and logic"""
    
    @staticmethod
    async def process_message(chat_request: ChatMessage) -> ChatResponse:
        """Main chat processing logic"""
        try:
            session_id = chat_request.session_id or str(uuid.uuid4())
            message = chat_request.message.lower().strip()

            # Initialize session if not exists
            session = db.get_session(session_id)
            if not session:
                session = db.create_session(session_id)

            context = {**session["context"], **chat_request.context}

            # Route to appropriate handler based on current step
            if session["step"] == "greeting":
                return await ChatHandler._handle_greeting(message, session_id, context)
            elif "report a dispute" in message or session["step"] == "main_menu":
                return await ChatHandler._handle_main_menu(message, session_id, session)
            elif "track existing dispute" in message:
                return await ChatHandler._handle_track_request(session_id, session)
            elif "get guidance" in message:
                return await ChatHandler._handle_guidance_request()
            elif "emergency help" in message:
                return await ChatHandler._handle_emergency_help()
            elif session["step"] == "dispute_type":
                return await ChatHandler._handle_dispute_type_selection(message, session_id, session)
            elif session["step"] == "bank_selection":
                return await ChatHandler._handle_bank_selection(message, session_id, session)
            elif session["step"] == "amount_input":
                return await ChatHandler._handle_amount_input(message, session_id, session)
            elif session["step"] == "date_input":
                return await ChatHandler._handle_date_input(message, session_id, session)
            elif session["step"] == "description_input":
                return await ChatHandler._handle_description_input(message, session_id, session)
            elif session["step"] == "card_info":
                return await ChatHandler._handle_card_info(message, session_id, session)
            elif session["step"] == "track_dispute":
                return await ChatHandler._handle_dispute_tracking(message)
            else:
                # Use AI for complex interactions
                ai_response = await OllamaService.get_ai_response(chat_request.message, context)
                return ChatResponse(
                    response=ai_response,
                    context={"session_id": session_id}
                )

        except Exception as e:
            logger.error(f"Chat processing error: {str(e)}")
            return ChatResponse(
                response="I apologize for the technical issue. Please try again or contact your bank directly for immediate assistance.",
                options=["Try Again", "Emergency Help"]
            )

    @staticmethod
    async def _handle_greeting(message: str, session_id: str, context: Dict[str, Any]) -> ChatResponse:
        """Handle greeting and initial interaction"""
        if any(word in message for word in ["hello", "hi", "help", "start"]):
            return ChatResponse(
                response="Hello! I'm your Banking Dispute Assistant. I can help you resolve banking disputes quickly and effectively. How can I assist you today?",
                options=MAIN_MENU_OPTIONS,
                context={"session_id": session_id, "step": "main_menu"}
            )
        else:
            ai_response = await OllamaService.get_ai_response(message, context)
            return ChatResponse(
                response=ai_response,
                options=MAIN_MENU_OPTIONS,
                context={"session_id": session_id}
            )

    @staticmethod
    async def _handle_main_menu(message: str, session_id: str, session: Dict) -> ChatResponse:
        """Handle main menu selections"""
        if "report a dispute" in message:
            session["step"] = "dispute_type"
            db.update_session(session_id, session)
            return ChatResponse(
                response="I'll help you report a dispute. What type of issue are you experiencing?",
                options=[dt.value for dt in DisputeType],
                context={"session_id": session_id}
            )
        return await ChatHandler._handle_greeting(message, session_id, {})

    @staticmethod
    async def _handle_track_request(session_id: str, session: Dict) -> ChatResponse:
        """Handle dispute tracking request"""
        session["step"] = "track_dispute"
        db.update_session(session_id, session)
        return ChatResponse(
            response="Please provide your dispute ID (starts with DSP) or reference number:",
            context={"session_id": session_id}
        )

    @staticmethod
    async def _handle_guidance_request() -> ChatResponse:
        """Handle guidance request"""
        return ChatResponse(
            response="""Here are some helpful resources for banking disputes:

• **Time is critical**: Contact your bank within 24 hours for unauthorized transactions
• **Gather evidence**: Save SMS alerts, receipts, and screenshots
• **File written complaint**: Submit formal dispute letter to your bank
• **Keep records**: Document all communications and reference numbers
• **Follow up**: Check status regularly and escalate if needed

Would you like detailed guidance for a specific type of dispute?""",
            options=GUIDANCE_TOPICS
        )

    @staticmethod
    async def _handle_emergency_help() -> ChatResponse:
        """Handle emergency help request"""
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
            options=BANKS
        )

    @staticmethod
    async def _handle_dispute_type_selection(message: str, session_id: str, session: Dict) -> ChatResponse:
        """Handle dispute type selection"""
        selected_type = None
        for dt in DisputeType:
            if dt.value.lower() in message or message in dt.value.lower():
                selected_type = dt
                break

        if selected_type:
            session["dispute_form"]["type"] = selected_type.value
            session["step"] = "bank_selection"
            db.update_session(session_id, session)

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

    @staticmethod
    async def _handle_bank_selection(message: str, session_id: str, session: Dict) -> ChatResponse:
        """Handle bank selection"""
        if any(bank.lower() in message for bank in BANKS):
            selected_bank = next(bank for bank in BANKS if bank.lower() in message)
            session["dispute_form"]["bank"] = selected_bank
            session["step"] = "amount_input"
            db.update_session(session_id, session)

            helpline = BANK_HELPLINES.get(selected_bank, "Contact bank directly")
            return ChatResponse(
                response=f"Bank: **{selected_bank}**\nHelpline: {helpline}\n\nWhat is the disputed amount? Please enter the amount in ₹ (e.g., 5000)",
                context={"session_id": session_id}
            )

    @staticmethod
    async def _handle_amount_input(message: str, session_id: str, session: Dict) -> ChatResponse:
        """Handle amount input"""
        amount_match = re.search(r'[\d,]+\.?\d*', message.replace(',', ''))
        if amount_match:
            amount = float(amount_match.group())
            session["dispute_form"]["amount"] = amount
            session["step"] = "date_input"
            db.update_session(session_id, session)

            return ChatResponse(
                response=f"Amount: ₹{amount:,.2f}\n\nWhen did this transaction occur? Please provide the date (e.g., 2024-01-15 or 15 Jan 2024)",
                context={"session_id": session_id}
            )
        else:
            return ChatResponse(
                response="Please enter a valid amount in numbers (e.g., 5000 or 1500.50)",
                context={"session_id": session_id}
            )

    @staticmethod
    async def _handle_date_input(message: str, session_id: str, session: Dict) -> ChatResponse:
        """Handle date input"""
        if any(char.isdigit() for char in message) and len(message) >= 8:
            session["dispute_form"]["date"] = message
            session["step"] = "description_input"
            db.update_session(session_id, session)

            return ChatResponse(
                response=f"Date: {message}\n\nPlease provide a brief description of the dispute and what happened:",
                context={"session_id": session_id}
            )
        else:
            return ChatResponse(
                response="Please provide a valid date (e.g., 2024-01-15, 15/01/2024, or 15 Jan 2024)",
                context={"session_id": session_id}
            )

    @staticmethod
    async def _handle_description_input(message: str, session_id: str, session: Dict) -> ChatResponse:
        """Handle description input"""
        session["dispute_form"]["description"] = message
        session["step"] = "card_info"
        db.update_session(session_id, session)

        return ChatResponse(
            response="Please provide the last 4 digits of the card involved (e.g., 1234). If not card-related, type 'N/A':",
            context={"session_id": session_id}
        )

    @staticmethod
    async def _handle_card_info(message: str, session_id: str, session: Dict) -> ChatResponse:
        """Handle card info input and create dispute"""
        session["dispute_form"]["cardlastfour"] = message if message.upper() != "N/A" else "N/A"

        try:
            dispute_form = DisputeForm(**session["dispute_form"])
            dispute_result = await DisputeService.create_dispute(dispute_form)

            # Clear session
            db.delete_session(session_id)

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

    @staticmethod
    async def _handle_dispute_tracking(message: str) -> ChatResponse:
        """Handle dispute tracking"""
        dispute_id = message.upper().strip()
        if dispute_id.startswith("DSP") and len(dispute_id) == 11:
            dispute = db.get_dispute(dispute_id)
            if dispute:
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
