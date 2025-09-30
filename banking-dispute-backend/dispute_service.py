
import logging
from typing import Dict, Any
from datetime import datetime
from models import DisputeForm, DisputeData, DisputeCreateResponse
from constants import Priority, DisputeType, BANK_HELPLINES
from database import db
from services import MCPServer

logger = logging.getLogger(__name__)


class DisputeService:
    """Service for managing dispute operations"""

    @staticmethod
    async def create_dispute(dispute_form: DisputeForm) -> Dict[str, Any]:
        """Create a new dispute with all business logic"""
        try:
            # Determine priority based on amount and type
            priority = DisputeService._determine_priority(dispute_form)

            # Create dispute data
            dispute_data = DisputeData(
                type=dispute_form.type,
                amount=dispute_form.amount,
                date=dispute_form.date,
                description=dispute_form.description,
                bank=dispute_form.bank,
                cardlastfour=dispute_form.cardlastfour,
                priority=priority
            )

            # Store in database
            created_dispute = db.create_dispute(dispute_data)

            # Get guidance steps from MCP server
            guidance_steps = await MCPServer.get_guidance_steps(dispute_form.type.value)

            # Determine estimated resolution time
            estimated_resolution = DisputeService._get_estimated_resolution(priority, dispute_form.type)

            # Get bank contact info
            bank_contact = BANK_HELPLINES.get(dispute_form.bank, "Contact your bank directly")

            return {
                "dispute_id": created_dispute.id,
                "status": "created",
                "priority": priority.value,
                "next_steps": guidance_steps,
                "estimated_resolution": estimated_resolution,
                "bank_contact": bank_contact,
                "created_at": created_dispute.createdAt
            }

        except Exception as e:
            logger.error(f"Dispute creation error: {str(e)}")
            raise Exception(f"Failed to create dispute: {str(e)}")

    @staticmethod
    def _determine_priority(dispute_form: DisputeForm) -> Priority:
        """Determine dispute priority based on type and amount"""

        # High priority for fraud-related disputes
        fraud_types = [
            DisputeType.UNAUTHORIZED, 
            DisputeType.MERCHANT_FRAUD, 
            DisputeType.CARD_SKIMMING
        ]

        if dispute_form.type in fraud_types:
            return Priority.HIGH

        # Priority based on amount
        if dispute_form.amount:
            if dispute_form.amount > 50000:
                return Priority.HIGH
            elif dispute_form.amount > 10000:
                return Priority.MEDIUM
            else:
                return Priority.LOW

        # Default priority for other types
        if dispute_form.type in [DisputeType.ATM_DISPUTE, DisputeType.FAILED_TRANSACTION]:
            return Priority.MEDIUM

        return Priority.LOW

    @staticmethod
    def _get_estimated_resolution(priority: Priority, dispute_type: DisputeType) -> str:
        """Get estimated resolution time based on priority and type"""

        # ATM disputes are typically faster
        if dispute_type == DisputeType.ATM_DISPUTE:
            return "2-3 business days"

        # High priority disputes
        if priority == Priority.HIGH:
            return "3-5 business days"
        elif priority == Priority.MEDIUM:
            return "5-7 business days"
        else:
            return "7-10 business days"

    @staticmethod
    async def get_dispute_guidance(dispute_type: str) -> Dict[str, Any]:
        """Get comprehensive guidance for dispute type"""
        try:
            # Get guidance steps
            steps = await MCPServer.get_guidance_steps(dispute_type)

            # Get complaint template
            template = await MCPServer.get_dispute_templates(dispute_type)

            # Get important documents
            documents = await MCPServer.get_important_documents(dispute_type)

            # Define time limits based on dispute type
            time_limits = DisputeService._get_time_limits(dispute_type)

            return {
                "dispute_type": dispute_type,
                "guidance_steps": steps,
                "complaint_template": template,
                "important_documents": documents,
                "time_limits": time_limits,
                "rbi_guidelines": DisputeService._get_rbi_guidelines(dispute_type)
            }

        except Exception as e:
            logger.error(f"Guidance retrieval error: {str(e)}")
            raise Exception(f"Failed to get guidance: {str(e)}")

    @staticmethod
    def _get_time_limits(dispute_type: str) -> Dict[str, str]:
        """Get time limits for different dispute types"""
        base_limits = {
            "report_to_bank": "Within 3 days for best results",
            "written_complaint": "Within 30 days of statement date",
            "rbi_ombudsman": "Within 30 days if bank doesn't respond",
            "chargeback_eligibility": "Within 120 days for card transactions"
        }

        if dispute_type == "Unauthorized Transaction":
            base_limits.update({
                "report_to_bank": "Within 3 days for zero liability",
                "card_blocking": "Immediately upon discovery",
                "police_complaint": "Within 24 hours for fraud cases"
            })
        elif dispute_type == "ATM Dispute":
            base_limits.update({
                "report_to_bank": "Within 30 minutes to 2 hours for best results",
                "written_complaint": "Within 30 days"
            })
        elif dispute_type == "Double Debit / Duplicate Charge":
            base_limits.update({
                "merchant_contact": "Within 2-3 days",
                "bank_dispute": "After 7 days if merchant unresponsive"
            })

        return base_limits

    @staticmethod
    def _get_rbi_guidelines(dispute_type: str) -> Dict[str, str]:
        """Get relevant RBI guidelines for dispute type"""
        guidelines = {
            "zero_liability": "Customers have zero liability for unauthorized electronic transactions if reported within 3 days",
            "limited_liability": "Limited liability of ₹10,000 if reported within 4-7 days",
            "resolution_timeline": "Banks must resolve disputes within 90 days",
            "ombudsman": "Approach Banking Ombudsman if bank doesn't respond within 30 days"
        }

        if dispute_type == "Unauthorized Transaction":
            guidelines.update({
                "immediate_action": "Bank must block card/account immediately upon reporting",
                "investigation": "Bank must complete investigation within 90 days",
                "provisional_credit": "Provisional credit within 10 days for amounts above ₹25,000"
            })
        elif dispute_type == "ATM Dispute":
            guidelines.update({
                "auto_reversal": "Failed ATM transactions should be auto-reversed within 5 days",
                "compensation": "₹100 per day compensation after 5 days for ATM failures"
            })

        return guidelines

    @staticmethod
    def get_dispute_status_update(dispute_id: str) -> Dict[str, Any]:
        """Get detailed dispute status with timeline"""
        dispute = db.get_dispute(dispute_id)
        if not dispute:
            raise Exception("Dispute not found")

        timeline = db.get_dispute_timeline(dispute_id)

        # Calculate progress percentage
        progress = DisputeService._calculate_progress(dispute.status, dispute.priority)

        return {
            "dispute": dispute,
            "timeline": timeline,
            "progress_percentage": progress,
            "next_action": DisputeService._get_next_action(dispute),
            "estimated_completion": DisputeService._get_estimated_completion(dispute)
        }

    @staticmethod
    def _calculate_progress(status, priority) -> int:
        """Calculate dispute progress percentage"""
        status_progress = {
            "submitted": 25,
            "under_review": 60,
            "resolved": 100,
            "escalated": 80
        }
        return status_progress.get(status.value, 0)

    @staticmethod
    def _get_next_action(dispute: DisputeData) -> str:
        """Get next recommended action for dispute"""
        if dispute.status.value == "submitted":
            return "Wait for bank acknowledgment (expected within 2 hours)"
        elif dispute.status.value == "under_review":
            return "Bank is investigating. You can follow up after 3-5 days"
        elif dispute.status.value == "escalated":
            return "Contact Banking Ombudsman if no response in 30 days"
        else:
            return "No further action required"

    @staticmethod
    def _get_estimated_completion(dispute: DisputeData) -> str:
        """Get estimated completion date"""
        created_date = datetime.fromisoformat(dispute.createdAt.replace('Z', '+00:00').split('+')[0])

        if dispute.priority == Priority.HIGH:
            days_to_add = 5
        elif dispute.priority == Priority.MEDIUM:
            days_to_add = 7
        else:
            days_to_add = 10

        from datetime import timedelta
        estimated_date = created_date + timedelta(days=days_to_add)
        return estimated_date.strftime("%Y-%m-%d")
