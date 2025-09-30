
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from pymongo.collection import Collection
import logging
from models import DisputeData, DisputeStatus, Priority, SessionData, UsersDB
from constants import DisputeType
logger = logging.getLogger(__name__)


class Database:
    
    def __init__(self, db):
        self.db = db
        self.disputes: Dict[str, DisputeData] = {}
        self.chat_sessions: Dict[str, Dict] = {}
    
    # Dispute operations
    def create_dispute(self, dispute: DisputeData) -> DisputeData:
        self.disputes[dispute.id] = dispute
        return dispute
    
    def get_dispute(self, dispute_id: str) -> Optional[DisputeData]:
        return self.disputes.get(dispute_id)
    
    def list_disputes(self, status: Optional[DisputeStatus] = None, 
                     bank: Optional[str] = None) -> List[DisputeData]:
        filtered_disputes = list(self.disputes.values())
        
        if status:
            filtered_disputes = [d for d in filtered_disputes if d.status == status]
        if bank:
            filtered_disputes = [d for d in filtered_disputes if d.bank.lower() == bank.lower()]
            
        return filtered_disputes
    
    def update_dispute_status(self, dispute_id: str, status: DisputeStatus) -> Optional[DisputeData]:
        if dispute_id in self.disputes:
            self.disputes[dispute_id].status = status
            return self.disputes[dispute_id]
        return None
    
    def get_dispute_summary(self) -> Dict:
        return {
            "by_status": {status.value: len([d for d in self.disputes.values() if d.status == status])
                          for status in DisputeStatus},
            "by_priority": {priority.value: len([d for d in self.disputes.values() if d.priority == priority])
                            for priority in Priority}
        }
    
    def get_dispute_timeline(self, dispute_id: str) -> List[Dict]:
        dispute = self.get_dispute(dispute_id)
        if not dispute:
            return []
            
        base_time = datetime.fromisoformat(dispute.createdAt.replace('Z', '+00:00').split('+')[0])
        
        timeline = [
            {
                "date": dispute.createdAt, 
                "status": "Submitted", 
                "description": "Dispute submitted successfully"
            },
            {
                "date": (base_time + timedelta(hours=2)).isoformat(),
                "status": "Acknowledged", 
                "description": "Bank acknowledged receipt"
            }
        ]
        
        if dispute.status in [DisputeStatus.UNDER_REVIEW, DisputeStatus.RESOLVED]:
            timeline.append({
                "date": (base_time + timedelta(days=1)).isoformat(),
                "status": "Under Review", 
                "description": "Investigation started"
            })
        
        if dispute.status == DisputeStatus.RESOLVED:
            timeline.append({
                "date": (base_time + timedelta(days=5)).isoformat(),
                "status": "Resolved", 
                "description": "Dispute resolved successfully"
            })
            
        return timeline
    
    def create_session(self, session_id: str) -> Dict:
        self.chat_sessions[session_id] = {
            "step": "greeting",
            "dispute_form": {},
            "context": {}
        }
        return self.chat_sessions[session_id]
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.chat_sessions.get(session_id)
    
    def update_session(self, session_id: str, session_data: Dict) -> Dict:
        self.chat_sessions[session_id] = session_data
        return session_data
    
    def delete_session(self, session_id: str) -> bool:
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            return True
        return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        if len(self.chat_sessions) > 100:
            session_ids = list(self.chat_sessions.keys())
            for session_id in session_ids[:len(session_ids)//2]:
                del self.chat_sessions[session_id]

    def get_user_by_email(self, email: str):
        user_data = self.db.users.find_one({"email": email})
        if not user_data:
            return None
        user_data.pop("_id")
        return user_data
    
    def save_user(self, userdata: UsersDB):
        try:
            result = self.db.users.insert_one(userdata)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Failed to save user: {e}")
            return None


